import streamlit as st
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import japanize_matplotlib
import io

# ファイルの読み込みをキャッシュ化
@st.cache_data
def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

def main():
    st.set_page_config(page_title="t検定アプリ", layout="centered")
    st.title("📊 2群のt検定アプリ")
    
    # サイドバーに設定を配置
    st.sidebar.header("⚙️ 検定の基本設定")
    is_paired_str = st.sidebar.radio(
        "データの「対応」の有無",
        ["対応なし（独立2群・別区画など）", "対応あり（同一区画の前後比較など）"],
        help="異なるグループを比較する場合は「対応なし」、同じ対象の処理前・処理後などを比較する場合は「対応あり」を選びます。"
    )
    is_paired = is_paired_str == "対応あり（同一区画の前後比較など）"

    tab1, tab2, tab3 = st.tabs(["📊 検定アプリ", "📖 用語・理論の解説", "📗 Excelでの計算方法"])
    
    # ==========================================
    # タブ1: 検定アプリ本体
    # ==========================================
    with tab1:
        st.subheader("📂 データの準備")

        input_method = st.radio(
            "データの入力方法を選んでください", 
            ["📋 Excelから直接コピペ (おすすめ)", "📥 ファイルをアップロード", "🌱 サンプルデータで試す"], 
            horizontal=True
        )
        
        df_input = pd.DataFrame()
        
        # --------------------------------------------------
        # 入力パターンの処理
        # --------------------------------------------------
        if input_method == "📋 Excelから直接コピペ (おすすめ)":
            pasted_text = st.text_area(
                "Excelから2つのグループのデータ（2列分）をコピーして、ここに貼り付けてください。\n※1行目はグループ名（列名）として認識されます。", 
                height=150,
                placeholder="ここに Ctrl+V (Macは Cmd+V) で貼り付け"
            )
            if pasted_text:
                try:
                    df_raw = pd.read_csv(io.StringIO(pasted_text), sep='\t')
                    if len(df_raw.columns) >= 2:
                        df_input = pd.DataFrame({"グループA": df_raw.iloc[:, 0], "グループB": df_raw.iloc[:, 1]})
                        st.success("📋 コピペデータを読み込みました！")
                    else:
                        st.warning("データが2列以上ありません。")
                        df_input = pd.DataFrame({"グループA": pd.Series(dtype="float"), "グループB": pd.Series(dtype="float")})
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
                    df_input = pd.DataFrame({"グループA": pd.Series(dtype="float"), "グループB": pd.Series(dtype="float")})
            else:
                df_input = pd.DataFrame({"グループA": pd.Series([None] * 10, dtype="float"), "グループB": pd.Series([None] * 10, dtype="float")})

        elif input_method == "📥 ファイルをアップロード":
            uploaded_file = st.file_uploader("Excelファイル (.xlsx) または CSVファイル (.csv)", type=["xlsx", "xls", "csv"])
            if uploaded_file is None:
                df_input = pd.DataFrame({"グループA": pd.Series([None] * 10, dtype="float"), "グループB": pd.Series([None] * 10, dtype="float")})
            else:
                try:
                    df_raw = load_data(uploaded_file)
                    if len(df_raw.columns) >= 2:
                        df_input = pd.DataFrame({"グループA": df_raw.iloc[:, 0], "グループB": df_raw.iloc[:, 1]})
                        st.success(f"📄 「{uploaded_file.name}」を読み込みました！")
                    else:
                        st.warning("データが2列以上ありません。")
                        df_input = pd.DataFrame({"グループA": pd.Series(dtype="float"), "グループB": pd.Series(dtype="float")})
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
                    df_input = pd.DataFrame({"グループA": pd.Series(dtype="float"), "グループB": pd.Series(dtype="float")})

        else:
            if is_paired:
                st.info("💡 **サンプルデータ（対応あり）**\n\n「同一区画」における処理前と処理後の数値を比較します。")
                df_input = pd.DataFrame({
                    "処理前": pd.Series([12.5, 13.0, 11.8, 14.2, 12.1] + [None]*5, dtype="float"),
                    "処理後": pd.Series([15.2, 14.8, 14.0, 16.5, 15.0] + [None]*5, dtype="float")
                })
            else:
                st.info("💡 **サンプルデータ（対応なし）**\n\n「新しい肥料をまいた5区画」と「従来のまま（肥料なし）の5区画」の収量（kg）を比較します。")
                df_input = pd.DataFrame({
                    "肥料あり (処理)": pd.Series([150, 130, 180, 160, 170] + [None]*5, dtype="float"),
                    "肥料なし (未処理)": pd.Series([200, 250, 220, 230, 190] + [None]*5, dtype="float")
                })

        edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)
        st.divider()
        
        # ==========================================
        # 検定の実行セクション
        # ==========================================
        st.subheader("⚙️ 検定の実行")
        
        col_names = edited_df.columns.tolist()
        col_a_name = col_names[0] if len(col_names) > 0 else "グループA"
        col_b_name = col_names[1] if len(col_names) > 1 else "グループB"
        
        # データのクレンジング（対応の有無で処理を変える）
        if is_paired:
            st.info("※ 「対応あり」の場合、ペアになっていない（片方が空欄の）行は計算から自動的に除外されます。")
            clean_df = edited_df.dropna(subset=[col_a_name, col_b_name])
            group_a = clean_df[col_a_name].values
            group_b = clean_df[col_b_name].values
        else:
            group_a = edited_df[col_a_name].dropna().values
            group_b = edited_df[col_b_name].dropna().values
        
        # 対応なしの場合のみ、等分散の仮定オプションを表示
        assume_equal_var = False
        if not is_paired:
            assume_equal_var = st.checkbox(
                "2群の分散が等しいと仮定する（Studentのt検定を適用）", 
                value=False,
                help="等分散性の検定結果で「等分散とみなせる」場合のみチェックを入れます。現代統計学では常にチェックを外してWelchのt検定を行うのが主流です。"
            )
        
        if st.button("検定を実行する", type="primary"):
            if len(group_a) < 2 or len(group_b) < 2:
                st.error("⚠️ 検定を実行するには、各グループに少なくとも2つ以上のデータが必要です。")
            else:
                # ------------------------------------------
                # 1. 対応なしの場合のみ、等分散性の検定 (Levene検定) を実行
                # ------------------------------------------
                if not is_paired:
                    st.subheader("🔍 1. 前提条件の確認（等分散性の検定）")
                    levene_stat, levene_p = stats.levene(group_a, group_b)
                    
                    st.caption("適用した手法: **Levene（ルビーン）検定**")
                    l_col1, l_col2 = st.columns(2)
                    l_col1.metric(label="検定統計量", value=f"{levene_stat:.4f}")
                    l_col2.metric(label="p値", value=f"{levene_p:.4f}")
                    
                    if levene_p < 0.05:
                        st.warning("⚠️ **p < 0.05** です。\n\n2つのグループのばらつき（分散）には**有意な差があります**。Studentのt検定は適さないため、設定のチェックを外して**Welchのt検定**を実行してください。")
                    else:
                        st.success("✅ **p ≥ 0.05** です。\n\n2つのグループのばらつき（分散）に**有意な差は認められません（等分散とみなせます）**。設定にチェックを入れて**Studentのt検定**を実行しても構いません。")
                    
                    st.info("※ 補足: 近年の統計学では、事前の等分散検定を行わず、最初から外れ値や非等分散に強い「Welchのt検定」を実施することが推奨されています。")
                    st.divider()

                # ------------------------------------------
                # 2. t検定の実行
                # ------------------------------------------
                st.subheader("📝 2. t検定結果")
                
                if is_paired:
                    test_name = "対応のあるt検定 (Paired t-test)"
                    t_stat, p_value = stats.ttest_rel(group_a, group_b)
                else:
                    test_name = "Studentのt検定" if assume_equal_var else "Welchのt検定"
                    t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=assume_equal_var)
                
                st.caption(f"適用した手法: **{test_name}**")
                
                col1, col2 = st.columns(2)
                col1.metric(label="t値 (t-statistic)", value=f"{t_stat:.4f}")
                col2.metric(label="p値 (p-value)", value=f"{p_value:.4f}")
                
                if p_value < 0.05:
                    st.success(f"✅ **p < 0.05** です。\n\n「{col_a_name}」と「{col_b_name}」の平均値には**統計的に有意な差がある**と言えます。")
                else:
                    st.info(f"➖ **p ≥ 0.05** です。\n\n「{col_a_name}」と「{col_b_name}」の平均値に**統計的な有意差は認められません**。")
                
                st.divider()

                # ------------------------------------------
                # 3. グラフの描画
                # ------------------------------------------
                st.subheader("📊 3. データの分布")
                plot_data = pd.DataFrame({
                    "値": list(group_a) + list(group_b),
                    "グループ": [col_a_name] * len(group_a) + [col_b_name] * len(group_b),
                    "ペアID": list(range(len(group_a))) + list(range(len(group_b))) # ペアごとのIDを振る
                })
                
                fig, ax = plt.subplots(figsize=(7, 5))
                
                if is_paired:
                    # 対応ありの場合は推移がわかるように線を引く
                    sns.pointplot(x="グループ", y="値", hue="ペアID", data=plot_data, ax=ax, palette="dark:gray", legend=False, markers="o", linestyles="-", alpha=0.6)
                    plt.title(f"{col_a_name}から{col_b_name}への推移（対応のあるデータ）", fontsize=14)
                else:
                    # 対応なしの場合は箱ひげ図＋スウォームプロット
                    sns.boxplot(x="グループ", y="値", data=plot_data, ax=ax, palette="pastel")
                    sns.swarmplot(x="グループ", y="値", data=plot_data, ax=ax, color=".25", size=6)
                    plt.title(f"{col_a_name}と{col_b_name}のデータのばらつき", fontsize=14)
                
                plt.ylabel("値")
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                st.pyplot(fig)

    # ==========================================
    # タブ2: 用語・理論の解説
    # ==========================================
    with tab2:
        st.subheader("📖 t検定の基礎知識")
        st.write("""
        #### 1. 「対応のあるデータ」と「対応のないデータ」
        t検定は、データの性質によって使う計算式が異なります。
        * **対応のないデータ（独立2群）**: 別のグループを比較する場合（例：AクラスとBクラスのテストの点数、新品種と従来品種の収量）。
        * **対応のあるデータ**: 全く同じ対象を2回測定して比較する場合（例：同じ患者の「薬を飲む前」と「飲んだ後」、同じ農場の「去年」と「今年」）。ペアごとの「差」に注目して検定を行います。
        
        #### 2. Welchのt検定とStudentのt検定（対応なしの場合）
        * **Student（スチューデント）のt検定**: 2つのグループのデータのばらつき（分散）が「等しい」という前提のもとで行う検定です。
        * **Welch（ウェルチ）のt検定**: 2つのグループのばらつきが「等しくなくても」正確に計算できる検定です。
        
        #### 3. 等分散性の検定とは？
        「Studentのt検定」を行う前に、「本当に2つのグループのばらつきは同じと言えるのか？」を確認するための検定です。本アプリでは**Levene（ルビーン）検定**を採用しています。
        * **p値が0.05未満**: ばらつきに差がある（非等分散） ➡ **Welchのt検定**を使うべき
        * **p値が0.05以上**: ばらつきに差がない（等分散） ➡ **Studentのt検定**を使ってもよい
        
        **⚠️ 注意点（現代のベストプラクティス）**
        かつては「等分散検定をしてからt検定を選ぶ」のが主流でしたが、現在では「2段階検定を行うと結果的にエラー確率が上がってしまう」ため、**事前の等分散検定は行わず、最初からWelchのt検定を無条件で使用する**ことが世界の統計学の標準となっています。
        """)

    # ==========================================
    # タブ3: Excelでの計算方法
    # ==========================================
    with tab3:
        st.subheader("📗 Excelでの計算方法")
        st.write("""
        ### 1. 等分散性の検定 (F検定) ※対応なしの場合のみ
        ExcelではLevene検定の代わりに、より簡易的なF検定関数が用意されています。
        
        `=F.TEST(配列1, 配列2)`
        
        * 結果（p値）が 0.05 未満なら「非等分散」、0.05 以上なら「等分散」と判定します。
        
        ### 2. t検定
        使用する関数は **`T.TEST`** 関数です。
        
        `=T.TEST(配列1, 配列2, 尾部, 検定の種類)`
        
        1. **配列1 / 配列2**: 比較したいデータの範囲
        2. **尾部**: 基本的に **`2`**（両側検定）を指定
        3. **検定の種類**: これが重要です！
           * **`1`** を指定 ➡ **対応のあるt検定**
           * **`2`** を指定 ➡ **Studentのt検定** (対応なし・等分散)
           * **`3`** を指定 ➡ **Welchのt検定** (対応なし・非等分散) ※対応なしの場合はこれを推奨
        """)

if __name__ == "__main__":
    main()
