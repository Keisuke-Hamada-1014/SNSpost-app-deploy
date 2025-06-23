import streamlit as st
import openai
from datetime import datetime, date
import json
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
from urllib.parse import urlparse

# .envファイルの読み込み
load_dotenv()

# 環境変数の取得
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEYが設定されていません。環境変数を設定してください。")
    st.stop()

# ページ設定
st.set_page_config(
    page_title="SNS投稿ジェネレーター AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSS - ダークテーマで知的なデザイン
st.markdown("""
<style>
    /* ベースカラー設定 */
    :root {
        --primary-color: #4f46e5;
        --primary-hover: #4338ca;
        --secondary-color: #6366f1;
        --accent-color: #10b981;
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --surface: #475569;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border-color: #475569;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
    }

    /* 全体のベース設定 */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #1a202c 100%);
        color: var(--text-primary);
    }

    /* メインコンテナ */
    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* ヘッダー */
    .main-header {
        text-align: center;
        padding: 3rem 0 2rem 0;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 50%, var(--accent-color) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        text-align: center;
        color: var(--text-secondary);
        font-size: 1.2rem;
        margin-bottom: 3rem;
        font-weight: 300;
    }

    /* 入力フォーム */
    .stTextInput > div > div > input {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border: 2px solid var(--border-color);
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 16px;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }

    .stSelectbox > div > div > div {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border: 2px solid var(--border-color);
        border-radius: 12px;
    }

    .stTextArea textarea {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border: 2px solid var(--border-color);
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 16px;
    }

    .stDateInput > div > div > input {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border: 2px solid var(--border-color);
        border-radius: 12px;
    }

    /* ボタン */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 16px 32px;
        font-size: 18px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(79, 70, 229, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(79, 70, 229, 0.4);
    }

    /* トーン表示 */
    .tone-display {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border-left: 4px solid var(--primary-color);
        padding: 2rem;
        margin: 2rem 0;
        border-radius: 0 16px 16px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .tone-display strong {
        color: var(--primary-color);
        font-weight: 700;
    }

    /* 投稿カード */
    .post-card {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }

    .post-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
        border-color: var(--primary-color);
    }
    
    .post-title {
        color: var(--primary-color);
        font-weight: 700;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    
    .post-content {
        line-height: 1.8;
        color: var(--text-primary);
        font-size: 16px;
        white-space: pre-wrap;
        background: var(--bg-primary);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 3px solid var(--accent-color);
    }

    /* コピーボタン */
    .copy-button {
        background: linear-gradient(135deg, var(--accent-color) 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
    }

    .copy-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
    }

    .copy-button:active {
        transform: translateY(0);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
    }

    .streamlit-expanderContent {
        background-color: var(--bg-secondary);
        border-radius: 0 0 12px 12px;
        padding: 0 1rem 1rem 1rem;
    }

    /* アラート */
    .stAlert {
        background-color: var(--bg-secondary);
        border-radius: 12px;
        border-left: 4px solid var(--primary-color);
    }

    .stSuccess {
        border-left-color: var(--success);
    }

    .stError {
        border-left-color: var(--error);
    }

    .stWarning {
        border-left-color: var(--warning);
    }

    /* スピナー */
    .stSpinner {
        color: var(--primary-color);
    }

    /* フッター */
    .footer-note {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.9rem;
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border-color);
        font-style: italic;
    }

    /* ラベル */
    .stTextInput label, .stSelectbox label, .stTextArea label, .stDateInput label {
        color: var(--text-primary);
        font-weight: 600;
        margin-bottom: 8px;
    }

    /* ヘルプテキスト */
    .stTextInput .help, .stSelectbox .help, .stTextArea .help, .stDateInput .help {
        color: var(--text-muted);
        font-size: 0.85rem;
    }

    /* コードブロック */
    .stCode {
        background-color: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }

    /* 成功メッセージのアニメーション */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .fade-in {
        animation: fadeInUp 0.5s ease-out;
    }

    /* コピー成功アニメーション */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    .copy-success {
        animation: pulse 0.3s ease-in-out;
        background: linear-gradient(135deg, var(--success) 0%, #059669 100%) !important;
    }
</style>

<script>
// クリップボードにコピーする関数
function copyToClipboard(text, buttonId) {
    navigator.clipboard.writeText(text).then(function() {
        // ボタンのテキストを一時的に変更
        const button = document.getElementById(buttonId);
        const originalText = button.innerHTML;
        button.innerHTML = '✅ コピー完了!';
        button.classList.add('copy-success');
        
        // 2秒後に元に戻す
        setTimeout(function() {
            button.innerHTML = originalText;
            button.classList.remove('copy-success');
        }, 2000);
    }).catch(function(err) {
        console.error('コピーに失敗しました: ', err);
        alert('コピーに失敗しました。手動でコピーしてください。');
    });
}
</script>
""", unsafe_allow_html=True)

class OpenAIService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
    
    def analyze_tone(self, prompt: str) -> str:
        """トーン＆マナーを分析"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたはSNSマーケティングの専門家です。与えられたSNSアカウントURLから、そのアカウントに適したトーン＆マナーを分析してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"トーン分析エラー: {str(e)}")
    
    def generate_posts(self, prompt: str) -> List[Dict[str, str]]:
        """投稿を生成"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたはプロのSNSコンテンツクリエーターです。指定された形式で6種類のSNS投稿文案をJSON形式で生成してください。必ずJSON形式で返答してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.8
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # JSONの抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            # JSONをパース
            posts = json.loads(json_text)
            
            if not isinstance(posts, list):
                raise ValueError("投稿データが配列形式ではありません")
                
            return posts
            
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析エラー: {str(e)}")
        except Exception as e:
            raise Exception(f"投稿生成エラー: {str(e)}")

def validate_url(url: str) -> bool:
    """URLの妥当性をチェック"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_media_type_label(media_type: str) -> str:
    """メディアタイプのラベルを取得"""
    labels = {
        "X": "𝕏 (Twitter)",
        "Facebook": "📘 Facebook",
        "Instagram": "📸 Instagram", 
        "LinkedIn": "💼 LinkedIn"
    }
    return labels.get(media_type, media_type)

def get_character_limit(media_type: str) -> str:
    """メディアタイプ別の文字数制限を取得"""
    limits = {
        "X": "140文字以内",
        "Instagram": "300文字以内",
        "Facebook": "400文字以内",
        "LinkedIn": "400文字以内"
    }
    return limits.get(media_type, "400文字以内")

def create_copy_button(content: str, button_id: str) -> str:
    """コピーボタンのHTMLを生成"""
    escaped_content = content.replace('"', '&quot;').replace("'", "\\'").replace('\n', '\\n')
    return f"""
    <button 
        id="{button_id}" 
        class="copy-button" 
        onclick="copyToClipboard('{escaped_content}', '{button_id}')"
    >
        📋 コピー
    </button>
    """

def main():
    # メインヘッダー
    st.markdown('<h1 class="main-header">SNS投稿ジェネレーター AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">🤖 AIがあなたのアカウントの雰囲気に合わせて、魅力的なSNS投稿を複数パターン作成します</p>', unsafe_allow_html=True)
    
    # APIキーの設定
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEYが設定されていません。環境変数を設定してください。")
        st.stop()
    
    # セッション状態の初期化
    if 'analyzed_tone' not in st.session_state:
        st.session_state.analyzed_tone = None
    if 'generated_posts' not in st.session_state:
        st.session_state.generated_posts = None
    if 'loading' not in st.session_state:
        st.session_state.loading = False
    
    # 入力フォーム
    with st.container():
        st.markdown("### 📝 基本情報を入力してください")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            sns_url = st.text_input(
                "🔗 SNSアカウントURL *",
                placeholder="例: https://twitter.com/account",
                help="分析したいSNSアカウントのURLを入力してください"
            )
        
        with col2:
            media_type = st.selectbox(
                "📱 投稿媒体 *",
                options=["X", "Facebook", "Instagram", "LinkedIn"],
                format_func=get_media_type_label
            )
    
    col3, col4 = st.columns([1, 2])
    
    with col3:
        selected_date = st.date_input(
            "📅 投稿予定日 *",
            min_value=date.today(),
            help="投稿を予定している日付を選択してください"
        )
    
    with col4:
        user_request = st.text_area(
            "💡 追加の要望（任意）",
            placeholder="特別な要望があれば入力してください（キャンペーン情報、トーンの調整など）",
            height=100
        )
    
    # 生成ボタン
    if st.button("✨ 投稿を生成する", type="primary", use_container_width=True):
        # バリデーション
        if not sns_url:
            st.error("SNSアカウントのURLを入力してください。")
            return
        
        if not validate_url(sns_url):
            st.error("有効なURLを入力してください。例: https://twitter.com/account")
            return
        
        # 生成処理
        try:
            openai_service = OpenAIService(api_key)
            
            with st.spinner('🧠 AIが投稿を生成中...'):
                # Step 1: トーン＆マナー分析
                st.info("🔍 トーン＆マナーを分析中...")
                tone_prompt = f"""以下のSNSアカウントURLに基づき、その投稿にふさわしいと考えられるトーン＆マナーを簡潔に説明してください。例：企業アカウントであればプロフェッショナルで情報提供型、個人ブログであればカジュアルで思索的、など。URL: {sns_url}"""
                
                analyzed_tone = openai_service.analyze_tone(tone_prompt)
                st.session_state.analyzed_tone = analyzed_tone
                
                # Step 2: 投稿生成
                st.info("📝 投稿文案を生成中...")
                
                post_generation_parts = [
                    "あなたはプロのSNSコンテンツクリエーターです。",
                    "以下の情報に基づいて、6種類の異なるSNS投稿文案を作成してください。",
                    "# 基本情報",
                    f"- SNSアカウントURL: {sns_url} (このURLの過去の投稿からトーン＆マナーを推測・学習し、それに厳密に従ってください)",
                    f"- 投稿予定日: {selected_date.strftime('%Y年%m月%d日')}",
                    f"- 媒体の種類: {media_type}",
                    f"- 推奨されるトーン＆マナー: 「{analyzed_tone}」 (これは以前のステップで分析されたものです。厳密に従ってください)",
                ]
                
                if user_request:
                    post_generation_parts.append(f"- ユーザーからの追加の要望: {user_request}")
                
                post_generation_parts.extend([
                    "# 出力形式",
                    "必ず以下のJSON形式で、6種類の投稿文案を配列として返してください。",
                    "各投稿文案は、指定されたトーン＆マナーを厳守し、媒体の特性を考慮してください。",
                    "投稿文は一般の読者に適しており、ポジティブまたはニュートラルな内容にしてください。",
                    f"投稿文は簡潔に、{get_character_limit(media_type)} を目安にしてください。",
                    "トーンに自然な場合や媒体の特性上必要な場合を除き、ハッシュタグは多用しないでください。",
                    "生成される内容は、必ず日本語でお願いします。",
                    "JSONのキー名（\"title\", \"content\"）も英語のままにしてください。",
                    "```json",
                    "[",
                    "  {",
                    "    \"title\": \"① 通常の商品紹介\",",
                    "    \"content\": \"ここに商品やサービスを紹介する投稿文案...\"",
                    "  },",
                    "  {",
                    f"    \"title\": \"② 『{selected_date.strftime('%m月%d日')}』のモーメントに合わせた投稿\",",
                    f"    \"content\": \"ここに {selected_date.strftime('%m月%d日')} の季節感やイベントに合わせた投稿文案...\"",
                    "  },",
                    "  {",
                    "    \"title\": \"③ エンゲージメントを高める投稿（キャンペーン以外）\",",
                    "    \"content\": \"ここに質問を投げかけたり、共感を呼ぶような、エンゲージメント向上を目的とした投稿文案（キャンペーン情報は含めない）...\"",
                    "  },",
                    "  {",
                    "    \"title\": \"④ 直近のキャンペーンに関連した投稿\",",
                    "    \"content\": \"ここに現在実施中または近日開始予定のキャンペーン情報を盛り込んだ投稿文案...\"",
                    "  },",
                    "  {",
                    "    \"title\": \"⑤ ユニークで工夫を効かせた投稿\",",
                    "    \"content\": \"ここに通常とは異なる視点や表現で、読者の目を引くようなユニークな投稿文案...\"",
                    "  },",
                    "  {",
                    "    \"title\": \"⑥ 自由投稿\",",
                    "    \"content\": \"ここに上記カテゴリに当てはまらないが、アカウントの価値を高めるような自由な発想の投稿文案...\"",
                    "  }",
                    "]",
                    "```",
                    "上記のJSON構造を厳守してください。他のテキストは含めないでください。"
                ])
                
                post_generation_prompt = '\n'.join(post_generation_parts)
                generated_posts = openai_service.generate_posts(post_generation_prompt)
                st.session_state.generated_posts = generated_posts
                
                st.success("✅ 投稿の生成が完了しました！")
                
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")
    
    # 結果表示
    if st.session_state.analyzed_tone:
        st.markdown("### 🎯 認識されたトーン＆マナー")
        st.markdown(f'<div class="tone-display fade-in"><strong>🧠 AI分析結果:</strong><br>{st.session_state.analyzed_tone}</div>', unsafe_allow_html=True)
    
    if st.session_state.generated_posts:
        st.markdown("### 📝 生成された投稿文案")
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        
        for i, post in enumerate(st.session_state.generated_posts):
            with st.expander(f"📄 {post['title']}", expanded=True):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f'<div class="post-content">{post["content"]}</div>', unsafe_allow_html=True)
                
                with col2:
                    # JavaScriptを使った改良されたコピーボタン
                    copy_button_html = create_copy_button(post["content"], f"copy_btn_{i}")
                    st.markdown(copy_button_html, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # フッター
    st.markdown('<div class="footer-note">⚡ Powered by AI - 生成されたコンテンツは必ず内容を確認・調整してからご利用ください</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()