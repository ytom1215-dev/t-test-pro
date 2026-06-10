import streamlit as st
import pandas as pd
from scipy import stats

def main():
    st.set_page_config(page_title="t検定アプリ", layout="centered")
    st.title("📊 独立した2群のt検定アプリ")

    # タブの作成（3つに増加）
    tab1, tab2, tab3 = st.tabs(["📊 検定アプリ", "📖 用語・理論の解説", "📗 Excelでの計算方法"])

    # ==========================================
    # タブ1: 検定アプリのメイン機能
    # ==========================================
    with tab1:
        st.subheader("📂 データの準備")
        
        # サンプルデータの定義
        samples = {
            "自分で入力 (Excelからコピペ用)": pd.DataFrame({
                "グループA": [None] * 10,
                "グループB": [None] * 10
            }),
            "サンプル1: 有意差があるデータ (例: 新薬と偽薬)": pd.DataFrame({
                "グループA": [65, 68, 70, 72, 69, 75, 67, 71, 73, 66],
                "グループB": [55, 58, 54, 60, 57, 52, 59, 56, 61, 53]
            }),
            "サンプル2: 有意差がないデータ (例: 従来法AとB)": pd.DataFrame({
                "グループA": [60, 62, 58, 65, 61, 59, 63, 64, 57, 60],
                "グループB": [61, 63, 59, 64, 62, 60, 65, 63, 58, 61]
            })
        }

        # データソースの選択
        selected_option = st.selectbox("データソースを選択してください", list(samples.keys()))
        st.markdown("※ 下の表のセルをクリックして「**Ctrl+V (Cmd+V)**」で直接上書き貼り付けすることも可能です。")

        # データエディタの表示
        edited_df = st.data_editor(samples[selected_option], num_rows="dynamic", use_container_width=True)

        st.divider()

        # 検定のオプション設定
        st.subheader("⚙️ 検定の設定")
        col1, col2 = st.columns(2)

        with col1:
            test_type = st.radio(
                "t検定の種類",
                ["スチューデントのt検定 (等分散を仮定)", "ウェルチのt検定 (等分散を仮定しない)"],
                index=1 # デフォルトはウェルチ
            )
            is_equal_var = (test_type == "スチューデントのt検定 (等分散を仮定)")

        with col2:
            tail_type = st.radio(
                "両側 / 片側",
                ["両側検定", "片側検定 (A > B)", "片側検定 (A < B)"]
            )
            if tail_type == "両側検定":
                alt = "two-sided"
            elif tail_type == "片側検定 (A > B)":
                alt = "greater"
            else:
                alt = "less"

        # 検定の実行
        if st.button("🚀 検定を実行", type="primary"):
            group_a = pd.to_numeric(edited_df["グループA"], errors='coerce').dropna()
            group_b = pd.to_numeric(edited_df["グループB"], errors='coerce').dropna()

            if len(group_a) < 2 or len(group_b) < 2:
                st.error("エラー：各グループに少なくとも2つ以上の数値を入力してください。")
            else:
                try:
                    result = stats.ttest_ind(a=group_a, b=group_b, equal_var=is_equal_var, alternative=alt)

                    st.divider()
                    st.subheader("📝 分析結果")
                    
                    st.markdown("**【基本統計量】**")
                    stats_df = pd.DataFrame({
                        "データ数": [len(group_a), len(group_b)],
                        "平均値": [group_a.mean(), group_b.mean()],
                        "標準偏差": [group_a.std(ddof=1), group_b.std(ddof=1)]
                    }, index=["グループA", "グループB"])
                    st.dataframe(stats_df)

                    st.markdown("**【検定結果】**")
                    res_col1, res_col2 = st.columns(2)
                    res_col1.metric("t値", f"{result.statistic:.4f}")
                    res_col2.metric("p値", f"{result.pvalue:.4e}")

                    alpha = 0.05
                    if result.pvalue < alpha:
                        st.success(f"**結論:** 有意水準 {alpha*100}% で**有意差があります**。(p < 0.05)")
                    else:
                        st.info(f"**結論:** 有意水準 {alpha*100}% で**有意差は認められませんでした**。(p >= 0.05)")

                except Exception as e:
                    st.error(f"計算中にエラーが発生しました: {e}")

    # ==========================================
    # タブ2: 用語・理論の解説
    # ==========================================
    with tab2:
        st.header("📖 統計用語と検定の選び方")
        
        st.subheader("1. 両側検定と片側検定の違い")
        st.markdown("""
        * **両側検定 (Two-sided):** 2つのグループ間に**「何らかの差があるか（A ≠ B）」**を確かめます。どちらが大きいかは事前に想定しません。**基本的には両側検定を使用します。**
        * **片側検定 (One-sided):** 「AはBより大きい（A > B）」または「小さい（A < B）」という、**方向性を限定した仮説**を確かめます。物理的な制約や強い理論的背景がある場合のみ使用します。安易に「p値を小さくしたいから」という理由で片側検定を選ぶのは不適切です。
        """)

        st.divider()

        st.subheader("2. スチューデントとウェルチのt検定の違い")
        st.markdown("""
        * **スチューデントのt検定:** 2つのグループの**「ばらつき（分散）が等しい」**という前提（等分散性）が必要です。
        * **ウェルチのt検定:** 2つのグループの**「ばらつき（分散）が異なっていても使える」**手法です。等分散の場合でもスチューデントとほぼ同じ結果になるため、**現代の統計学では、基本的に常に「ウェルチのt検定」を使用することが推奨されています。**
        """)

        st.divider()

        st.subheader("3. t検定とF検定の違い")
        st.markdown("""
        * **t検定:** 2つのグループの**「平均値」**に差があるかを比較する検定です。（例：A組とB組のテストの平均点に差はあるか？）
        * **F検定:** 2つのグループの**「分散（ばらつき）」**に差があるかを比較する検定です。（例：A組とB組で、点数のばらつき具合に差はあるか？）
        """)
        
        st.info("""
        **💡 補足（事前検定の罠）：**
        昔は「まずF検定をして、等分散ならスチューデント、不等分散ならウェルチのt検定を行う」という2段階の手順（事前検定）が教えられていましたが、現在はこの方法は**推奨されていません**（多重性の問題によりエラー率が上がるため）。最初からウェルチのt検定を使用するのがベストプラクティスです。
        """)

    # ==========================================
    # タブ3: Excelでの計算方法 (T.TEST関数)
    # ==========================================
    with tab3:
        st.header("📗 Excelでのt検定 (T.TEST関数)")
        st.markdown("""
        Excel上ですぐにp値（有意確率）を出したい場合は、**`T.TEST`関数**を使うのが最も簡単です。

        ### 💡 T.TEST関数の基本構文
        任意のセルに以下のように入力します。
        """)
        
        st.code("=T.TEST(配列1, 配列2, 尾部, 検定の種類)", language="excel")
        
        st.markdown("""
        #### 引数の説明
        * **配列1, 配列2:** 比較したい2つのデータ範囲（例: `A2:A11`, `B2:B11`）
        * **尾部 (両側か片側か):** * `1` : 片側検定
            * **`2` : 両側検定（基本はこちらを使用）**
        * **検定の種類 (スチューデントかウェルチか):**
            * `1` : 対応のあるt検定
            * `2` : スチューデントのt検定（等分散を仮定）
            * **`3` : ウェルチのt検定（非等分散・推奨）**

        ---
        ### 📝 実践的な入力例
        データがA2〜A11、B2〜B11に入力されていると仮定した場合の例です。

        **① 両側検定 × ウェルチのt検定（最も標準的で推奨）**
        """)
        st.code("=T.TEST(A2:A11, B2:B11, 2, 3)", language="excel")

        st.markdown("**② 両側検定 × スチューデントのt検定**")
        st.code("=T.TEST(A2:A11, B2:B11, 2, 2)", language="excel")

        st.markdown("**③ 片側検定 × ウェルチのt検定**")
        st.code("=T.TEST(A2:A11, B2:B11, 1, 3)", language="excel")

        st.info("""
        **✅ 判定の目安:**
        関数の結果として表示される数値がそのまま **p値** になります。
        この値が `0.05` 未満であれば、「有意水準5%で有意差あり」と判断します。
        """)

if __name__ == "__main__":
    main()