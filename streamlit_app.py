import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pytrends.request import TrendReq
from datetime import datetime, date
import time

# ── ページ設定 ──────────────────────────────────────────────
st.set_page_config(
    page_title="Google Trends Japan Analyzer",
    layout="wide",
)

# ── カスタムCSS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}

/* ヘッダー */
.main-header {
    background: linear-gradient(135deg, #e8f4fd 0%, #fce4ec 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    border-left: 5px solid #e53935;
}

.main-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0 0 6px 0;
}

.main-header p {
    color: #555;
    margin: 0;
    font-size: 0.9rem;
}

/* カードスタイル */
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #f0f0f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    text-align: center;
}

/* セクションタイトル */
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a1a2e;
    padding: 8px 0 12px 0;
    border-bottom: 2px solid #e53935;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ランキングテーブル */
.rank-table {
    width: 100%;
    border-collapse: collapse;
}
.rank-table th {
    background: #fafafa;
    color: #666;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid #eee;
}
.rank-table td {
    padding: 9px 12px;
    border-bottom: 1px solid #f5f5f5;
    font-size: 0.88rem;
    color: #333;
}
.rank-table tr:last-child td { border-bottom: none; }
.rank-table tr:hover td { background: #fafafa; }

/* バッジ */
.badge-breakout {
    background: #fff3e0;
    color: #e65100;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
}
.badge-rise {
    background: #e8f5e9;
    color: #2e7d32;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
}

/* ヒント */
.info-box {
    background: #e3f2fd;
    border-left: 4px solid #1976d2;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    font-size: 0.82rem;
    color: #1565c0;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ── ヘッダー ────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>Google Trends Japan Analyzer</h1>
    <p>日本市場向け・都道府県別インサイトを含むトレンド分析ツール</p>
</div>
""", unsafe_allow_html=True)

# ── 入力フォーム ────────────────────────────────────────────
with st.container():
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

    with col1:
        keyword = st.text_input(
            "🔍 キーワード (Keyword)",
            placeholder="例: 仁川空港、韓国旅行",
            help="検索するキーワードを入力してください"
        )
    with col2:
        start_date = st.date_input(
            "開始日 (Start Date)",
            value=date(2026, 1, 1),
            min_value=date(2024, 1, 1),
            max_value=date.today(),
        )
    with col3:
        end_date = st.date_input(
            "終了日 (End Date)",
            value=date.today(),
            min_value=date(2024, 1, 2),
            max_value=date.today(),
        )
    with col4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        run = st.button("分析する", type="primary", use_container_width=True)

# ── バリデーション ──────────────────────────────────────────
if run:
    if not keyword:
        st.error("⚠️ キーワードを入力してください。")
        st.stop()
    if start_date >= end_date:
        st.error("⚠️ 開始日は終了日より前に設定してください。")
        st.stop()

    timeframe = f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"

    # ── データ取得 ──────────────────────────────────────────
    with st.spinner("Google Trendsからデータを取得中... 少々お待ちください"):
        try:
            pytrends = TrendReq(hl='ja-JP', tz=-540)
            pytrends.build_payload(
                kw_list=[keyword],
                cat=0,
                timeframe=timeframe,
                geo='JP',      # 日本限定
                gprop=''
            )

            # 1) 時系列データ
            iot = pytrends.interest_over_time()

            # 2) 都道府県別データ（少しウェイト）
            time.sleep(1)
            geo_data = pytrends.interest_by_region(
                resolution='REGION',   # 都道府県レベル
                inc_low_vol=True,
                inc_geo_code=False
            )

            # 3) 関連クエリ
            time.sleep(1)
            related = pytrends.related_queries()

        except Exception as e:
            st.error(f"❌ データ取得エラー: {e}\n\nしばらく時間をおいてから再試行してください（レート制限の可能性があります）。")
            st.stop()

    if iot.empty:
        st.warning("⚠️ 指定した期間・キーワードでデータが見つかりませんでした。")
        st.stop()

    iot = iot.drop(columns=['isPartial'], errors='ignore')

    # ── サマリー指標 ───────────────────────────────────────
    st.markdown("---")
    avg_val = int(iot[keyword].mean())
    max_val = int(iot[keyword].max())
    max_date = iot[keyword].idxmax().strftime('%Y年%m月%d日')
    min_val = int(iot[keyword].min())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("平均関心度", avg_val, help="期間中の平均スコア（0〜100）")
    c2.metric("最高スコア", max_val)
    c3.metric("ピーク日", max_date)
    c4.metric("最低スコア", min_val)

    # ── ① 時系列チャート ───────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">時系列トレンド（日本）</div>', unsafe_allow_html=True)

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=iot.index,
        y=iot[keyword],
        mode='lines',
        name=keyword,
        line=dict(color='#e53935', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(229,57,53,0.08)',
        hovertemplate='%{x|%Y/%m/%d}<br>関心度: <b>%{y}</b><extra></extra>',
    ))
    fig_line.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickformat='%Y/%m'),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', range=[0, 105], title='関心度スコア'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        font=dict(family='Noto Sans JP, sans-serif'),
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # ── ② 都道府県別 ───────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">都道府県別 関心度</div>', unsafe_allow_html=True)

    if geo_data.empty or geo_data[keyword].sum() == 0:
        st.info("都道府県別データは取得できませんでした（データ量が少ない可能性があります）。")
    else:
        geo_sorted = geo_data[[keyword]].sort_values(keyword, ascending=False)
        geo_sorted = geo_sorted[geo_sorted[keyword] > 0].reset_index()
        geo_sorted.columns = ['都道府県', '関心度']

        tab1, tab2 = st.tabs(["横棒グラフ", "ランキング表"])

        with tab1:
            fig_bar = px.bar(
                geo_sorted,
                x='関心度',
                y='都道府県',
                orientation='h',
                color='関心度',
                color_continuous_scale=['#ffcdd2', '#e53935', '#b71c1c'],
                text='関心度',
            )
            fig_bar.update_traces(textposition='outside', textfont_size=11)
            fig_bar.update_layout(
                height=max(400, len(geo_sorted) * 22),
                margin=dict(l=0, r=40, t=10, b=0),
                yaxis=dict(autorange='reversed'),
                coloraxis_showscale=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Noto Sans JP, sans-serif'),
                xaxis=dict(range=[0, 115]),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with tab2:
            medal = {0: '🥇', 1: '🥈', 2: '🥉'}
            rows = ""
            for i, row in geo_sorted.iterrows():
                rank_str = medal.get(i, f"{i+1}")
                bar_w = int(row['関心度'])
                rows += f"""
                <tr>
                    <td style="text-align:center;font-weight:600">{rank_str}</td>
                    <td>{row['都道府県']}</td>
                    <td>
                        <div style="background:#f5f5f5;border-radius:4px;overflow:hidden;height:10px;width:180px">
                            <div style="background:#e53935;height:100%;width:{bar_w}%;border-radius:4px"></div>
                        </div>
                    </td>
                    <td style="font-weight:600;color:#e53935">{row['関心度']}</td>
                </tr>"""
            st.markdown(f"""
            <table class="rank-table">
                <thead><tr>
                    <th style="width:50px">順位</th>
                    <th>都道府県</th>
                    <th>スコア分布</th>
                    <th>スコア</th>
                </tr></thead>
                <tbody>{rows}</tbody>
            </table>
            """, unsafe_allow_html=True)

    # ── ③ 関連クエリ ──────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">関連クエリ</div>', unsafe_allow_html=True)

    col_top, col_rise = st.columns(2)

    def render_query_table(df, score_col, badge_fn):
        if df is None or df.empty:
            st.info("データなし")
            return
        rows = ""
        for i, row in df.head(10).iterrows():
            badge = badge_fn(row[score_col])
            rows += f"<tr><td style='text-align:center;color:#999;font-size:0.8rem'>{i+1}</td><td>{row['query']}</td><td>{badge}</td></tr>"
        st.markdown(f"""
        <table class="rank-table">
            <thead><tr>
                <th style="width:40px">#</th>
                <th>クエリ</th>
                <th>スコア</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
        """, unsafe_allow_html=True)

    with col_top:
        st.markdown("**トップ関連クエリ**")
        top_df = related.get(keyword, {}).get('top')
        render_query_table(
            top_df.reset_index(drop=True) if top_df is not None else None,
            'value',
            lambda v: f'<span class="badge-rise">{int(v)}</span>'
        )

    with col_rise:
        st.markdown("**急上昇クエリ**")
        rise_df = related.get(keyword, {}).get('rising')
        def rise_badge(v):
            if str(v).lower() == 'breakout':
                return '<span class="badge-breakout">急上昇</span>'
            return f'<span class="badge-rise">+{int(v)}%</span>'
        render_query_table(
            rise_df.reset_index(drop=True) if rise_df is not None else None,
            'value',
            rise_badge
        )

    # ── フッター ──────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f"<div style='text-align:center;color:#aaa;font-size:0.78rem'>データソース: Google Trends (日本 / geo=JP, hl=ja-JP) ・ 期間: {timeframe}</div>",
        unsafe_allow_html=True
    )

else:
    st.markdown("""
    <div class="info-box">
        キーワードと期間を入力して「分析する」ボタンをクリックしてください。
        （例: キーワード = <b>韓国旅行</b>、期間 = 2025-01-01 〜 2025-12-31）
    </div>
    """, unsafe_allow_html=True)

