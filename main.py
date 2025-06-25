import streamlit as st
import openai
from datetime import datetime, date
import json
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
from urllib.parse import urlparse
import uuid

# .envファイルの読み込み
load_dotenv()

# 環境変数の取得
openai_api_key = os.getenv("OPENAI_API_KEY")
x_api_key = os.getenv("X_API_KEY")

if not openai_api_key:
    st.error("❌ OPENAI_API_KEYが設定されていません。環境変数を設定してください。")
    st.stop()

# ページ設定
st.set_page_config(
    page_title="𝕏 投稿ジェネレーター AI",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSS
from ui_styles import get_custom_css
st.markdown(get_custom_css(), unsafe_allow_html=True)

class OpenAIService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
    
    def analyze_tone(self, account_url: str, company_url: str = None) -> str:
        """OpenAI APIを使用してトーン＆マナーを分析"""
        try:
            prompt_parts = [
                "あなたはX（旧Twitter）のマーケティング専門家です。",
                f"指定されたXアカウント「{account_url}」の過去の投稿から、そのアカウントに適したトーン＆マナーを分析してください。",
                "分析する際は以下の観点を考慮してください：",
                "- 投稿の文体（カジュアル/フォーマル）",
                "- 絵文字の使用頻度と種類",
                "- ハッシュタグの使用パターン",
                "- フォロワーとの接し方",
                "- ブランドの個性や特徴",
                "- Xプラットフォーム特有の表現方法",
                "150文字以内で簡潔にまとめてください。"
            ]
            
            if company_url:
                prompt_parts.insert(-1, f"- 企業サイト「{company_url}」も参考にしてブランドイメージを理解してください。")
            
            prompt = "\n".join(prompt_parts)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたはX（旧Twitter）のマーケティング専門家です。指定されたアカウントの特徴を的確に分析し、簡潔に説明してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"トーン分析エラー: {str(e)}")
    
    def generate_posts(self, account_url: str, company_url: str, post_date: str, analyzed_tone: str, user_request: str = None) -> List[Dict[str, str]]:
        """改良されたプロンプトでX投稿を生成"""
        try:
            # アカウント名を推測
            account_name = account_url.split('/')[-1] if account_url else "unknown"
            
            prompt_parts = [
                "# 役割",
                f"あなたは {account_name} のXアカウントの中の人であり、ベテランのXマーケターです。",
                "",
                "# 指示", 
                f"参考項目を参考に{post_date}に投稿するX投稿テキストを6種類作成してください。",
                f"情報はX公式アカウントからのみ抽出してください。",
                "",
                "# コンテキスト",
                f"アカウント名: {account_name}",
                f"アカウントURL: {account_url}",
                f"媒体: X（旧Twitter）",
                f"投稿予定日: {post_date}",
                f"認識されたトーン&マナー: {analyzed_tone}",
            ]
            
            if company_url:
                prompt_parts.extend([
                    f"企業サイトURL: {company_url}",
                ])
            
            if user_request:
                prompt_parts.extend([
                    f"追加要望: {user_request}",
                ])
            
            prompt_parts.extend([
                "",
                "# 参考項目",
                "- X公式アカウントの過去投稿のトーン&マナーを厳密に参考",
                "- 認識されたトーン&マナーに従って一貫性を保つ",
                f"- {post_date}の季節感やタイミングを活用",
                "- Xプラットフォームの特性（280文字制限、リツイート文化等）を考慮",
                "",
                "# 注意事項",
                f"- 「{account_url}」の過去ポストを参照すること",
                f"- 「{account_url}」と「{company_url if company_url else 'N/A'}」以外から情報を参照しないこと",
            ])
            
            if company_url:
                prompt_parts.extend([
                    f"- 「{company_url}」から今発売中の商品のみを使うこと",
                    f"- 「{company_url}」に記載のない商品は使わないこと",
                ])
            
            prompt_parts.extend([
                "- 投稿文は280文字以内（X仕様）を厳守する",
                "- 日本語で作成する",
                "- ポジティブまたはニュートラルな内容にする",
                "- Xらしい簡潔で印象的な表現を心がける",
                "",
                "# 出力方法",
                "以下のJSON形式で6つの投稿テーマを作成してください：",
                "",
                "# 投稿テーマ",
                "- ①通常の商品紹介",
                f"- ②「{post_date}」のモーメントに合わせた投稿", 
                "- ③エンゲージメントを高める投稿。ただしキャンペーンには絡めないこと。",
                "- ④直近のキャンペーンに関連した投稿",
                "- ⑤ユニークで工夫を効かせた投稿",
                "- ⑥自由投稿",
                "",
                "必ず以下のJSON形式で返してください：",
                "[",
                "  {",
                "    \"title\": \"① 通常の商品紹介\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                f"    \"title\": \"② 『{post_date}』のモーメントに合わせた投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                "    \"title\": \"③ エンゲージメントを高める投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                "    \"title\": \"④ 直近のキャンペーンに関連した投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                "    \"title\": \"⑤ ユニークで工夫を効かせた投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                "    \"title\": \"⑥ 自由投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  }",
                "]"
            ])
            
            prompt = "\n".join(prompt_parts)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたはプロのXコンテンツクリエーターです。指定された形式で6種類のX投稿文案をJSON形式で生成してください。必ずJSON形式で返答してください。"},
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
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
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

def validate_x_url(url: str) -> bool:
    """XのURLかどうかをチェック"""
    if not validate_url(url):
        return False
    parsed = urlparse(url)
    return parsed.netloc.lower() in ['twitter.com', 'x.com', 'www.twitter.com', 'www.x.com']

def main():
    # メインヘッダー
    st.markdown('''
    <div class="hero-section">
        <div class="hero-content">
            <h1 class="hero-title">𝕏 投稿ジェネレーター AI</h1>
            <p class="hero-subtitle">🤖 OpenAI GPTがあなたのXアカウントの雰囲気に合わせて、魅力的な投稿を複数パターン作成します</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # セッション状態の初期化
    if 'analyzed_tone' not in st.session_state:
        st.session_state.analyzed_tone = None
    if 'generated_posts' not in st.session_state:
        st.session_state.generated_posts = None
    if 'loading' not in st.session_state:
        st.session_state.loading = False
    
    # 中央寄せの入力フォーム
    st.markdown('<div class="centered-container">', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        st.markdown("### 📝 基本情報を入力してください")
        
        # 中央寄せのための列配置
        col_left, col_center, col_right = st.columns([1, 3, 1])
        
        with col_center:
            sns_url = st.text_input(
                "🔗 XアカウントURL *",
                placeholder="例: https://x.com/PAPICO_JPN",
                help="分析したいXアカウントのURLを入力してください"
            )
            
            # 2列レイアウト
            date_col, company_col = st.columns([1, 2])
            
            with date_col:
                selected_date = st.date_input(
                    "📅 投稿予定日 *",
                    min_value=date.today(),
                    help="投稿を予定している日付を選択してください"
                )
            
            with company_col:
                company_url = st.text_input(
                    "🏢 企業サイトURL（任意）",
                    placeholder="例: https://jp.glico.com/ice/papico/products.html",
                    help="商品情報を参照する企業サイトのURLを入力してください"
                )
            
            user_request = st.text_area(
                "💡 追加の要望（任意）",
                placeholder="特別な要望があれば入力してください（キャンペーン情報、トーンの調整など）",
                height=100
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 生成ボタン（中央寄せ）
    st.markdown('<div class="generate-section">', unsafe_allow_html=True)
    
    button_col1, button_col2, button_col3 = st.columns([1, 2, 1])
    with button_col2:
        if st.button("✨ X投稿を生成する", type="primary", use_container_width=True):
            # バリデーション
            if not sns_url:
                st.error("XアカウントのURLを入力してください。")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            if not validate_x_url(sns_url):
                st.error("有効なX（旧Twitter）のURLを入力してください。例: https://x.com/account")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            if company_url and not validate_url(company_url):
                st.error("企業サイトURLが有効ではありません。")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            # 生成処理
            try:
                openai_service = OpenAIService(openai_api_key)
                
                with st.spinner('🤖 OpenAI GPTが投稿を生成中...'):
                    # Step 1: トーン＆マナー分析
                    st.info("🔍 トーン＆マナーを分析中...")
                    
                    analyzed_tone = openai_service.analyze_tone(sns_url, company_url)
                    st.session_state.analyzed_tone = analyzed_tone
                    
                    # Step 2: 投稿生成
                    st.info("📝 X投稿文案を生成中...")
                    
                    post_date = selected_date.strftime('%Y/%m/%d')
                    generated_posts = openai_service.generate_posts(
                        sns_url, company_url, post_date, analyzed_tone, user_request
                    )
                    st.session_state.generated_posts = generated_posts
                    
                    st.success("✅ X投稿の生成が完了しました！")
                    
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 結果表示
    if st.session_state.analyzed_tone:
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        st.markdown("### 🎯 認識されたトーン＆マナー")
        st.markdown(f'''
        <div class="tone-card">
            <div class="tone-header">
                <span class="tone-icon">🤖</span>
                <span class="tone-title">OpenAI GPT分析結果</span>
            </div>
            <div class="tone-content">
                {st.session_state.analyzed_tone}
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    if st.session_state.generated_posts:
        st.markdown("### 🐦 生成されたX投稿文案")
        
        for i, post in enumerate(st.session_state.generated_posts):
            # ユニークなIDを生成
            post_id = f"post_{i}_{uuid.uuid4().hex[:8]}"
            
            # 文字数カウント
            char_count = len(post["content"])
            char_color = "green" if char_count <= 280 else "red"
            
            st.markdown(f'''
            <div class="post-card">
                <div class="post-header">
                    <h4 class="post-title">{post['title']}</h4>
                    <div class="post-actions">
                        <span class="char-count" style="color: {char_color};">{char_count}/280文字</span>
                        <button class="copy-button" onclick="copyToClipboard('{post_id}')">
                            <span class="copy-icon">📋</span>
                            <span class="copy-text">コピー</span>
                        </button>
                    </div>
                </div>
                <div class="post-content" id="{post_id}">
                    {post["content"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # JavaScript for copy functionality
    st.markdown('''
    <script>
    function copyToClipboard(elementId) {
        const element = document.getElementById(elementId);
        const text = element.innerText || element.textContent;
        
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(function() {
                showCopySuccess();
            }).catch(function(err) {
                fallbackCopyTextToClipboard(text);
            });
        } else {
            fallbackCopyTextToClipboard(text);
        }
    }
    
    function fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";
        
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showCopySuccess();
        } catch (err) {
            console.error('コピーに失敗しました: ', err);
            alert('コピーに失敗しました。手動でコピーしてください。');
        }
        
        document.body.removeChild(textArea);
    }
    
    function showCopySuccess() {
        // 成功メッセージの表示
        const toast = document.createElement('div');
        toast.className = 'copy-toast';
        toast.innerHTML = '✅ コピーしました！';
        document.body.appendChild(toast);
        
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 2000);
    }
    </script>
    ''', unsafe_allow_html=True)
    
    # フッター
    st.markdown('''
    <div class="footer">
        <p>🤖 Powered by OpenAI GPT - 生成されたコンテンツは必ず内容を確認・調整してからご利用ください</p>
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_tone(self, account_url: str, company_url: str = None) -> str:
        """Grok APIを使用してトーン＆マナーを分析"""
        try:
            prompt_parts = [
                "あなたはX（旧Twitter）のマーケティング専門家です。",
                f"指定されたXアカウント「{account_url}」の過去の投稿から、そのアカウントに適したトーン＆マナーを分析してください。",
                "分析する際は以下の観点を考慮してください：",
                "- 投稿の文体（カジュアル/フォーマル）",
                "- 絵文字の使用頻度と種類",
                "- ハッシュタグの使用パターン",
                "- フォロワーとの接し方",
                "- ブランドの個性や特徴",
                "- Xプラットフォーム特有の表現方法",
                "150文字以内で簡潔にまとめてください。"
            ]
            
            if company_url:
                prompt_parts.insert(-1, f"- 企業サイト「{company_url}」も参考にしてブランドイメージを理解してください。")
            
            prompt = "\n".join(prompt_parts)
            
            payload = {
                "messages": [
                    {"role": "system", "content": "あなたはX（旧Twitter）のマーケティング専門家です。指定されたアカウントの特徴を的確に分析し、簡潔に説明してください。"},
                    {"role": "user", "content": prompt}
                ],
                "model": "grok-beta",
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"トーン分析エラー: {str(e)}")
    
    def generate_posts(self, account_url: str, company_url: str, post_date: str, analyzed_tone: str, user_request: str = None) -> List[Dict[str, str]]:
        """改良されたプロンプトでX投稿を生成"""
        try:
            # アカウント名を推測
            account_name = account_url.split('/')[-1] if account_url else "unknown"
            
            prompt_parts = [
                "# 役割",
                f"あなたは {account_name} のXアカウントの中の人であり、ベテランのXマーケターです。",
                "",
                "# 指示", 
                f"参考項目を参考に{post_date}に投稿するX投稿テキストを6種類作成してください。",
                f"情報はX公式アカウントからのみ抽出してください。",
                "",
                "# コンテキスト",
                f"アカウント名: {account_name}",
                f"アカウントURL: {account_url}",
                f"媒体: X（旧Twitter）",
                f"投稿予定日: {post_date}",
                f"認識されたトーン&マナー: {analyzed_tone}",
            ]
            
            if company_url:
                prompt_parts.extend([
                    f"企業サイトURL: {company_url}",
                ])
            
            if user_request:
                prompt_parts.extend([
                    f"追加要望: {user_request}",
                ])
            
            prompt_parts.extend([
                "",
                "# 参考項目",
                "- X公式アカウントの過去投稿のトーン&マナーを厳密に参考",
                "- 認識されたトーン&マナーに従って一貫性を保つ",
                f"- {post_date}の季節感やタイミングを活用",
                "- Xプラットフォームの特性（280文字制限、リツイート文化等）を考慮",
                "",
                "# 注意事項",
                f"- 「{account_url}」の過去ポストを参照すること",
                f"- 「{account_url}」と「{company_url if company_url else 'N/A'}」以外から情報を参照しないこと",
            ])
            
            if company_url:
                prompt_parts.extend([
                    f"- 「{company_url}」から今発売中の商品のみを使うこと",
                    f"- 「{company_url}」に記載のない商品は使わないこと",
                ])
            
            prompt_parts.extend([
                "- 投稿文は280文字以内（X仕様）を厳守する",
                "- 日本語で作成する",
                "- ポジティブまたはニュートラルな内容にする",
                "- Xらしい簡潔で印象的な表現を心がける",
                "",
                "# 出力方法",
                "以下のJSON形式で6つの投稿テーマを作成してください：",
                "",
                "# 投稿テーマ",
                "- ①通常の商品紹介",
                f"- ②「{post_date}」のモーメントに合わせた投稿", 
                "- ③エンゲージメントを高める投稿。ただしキャンペーンには絡めないこと。",
                "- ④直近のキャンペーンに関連した投稿",
                "- ⑤ユニークで工夫を効かせた投稿",
                "- ⑥自由投稿",
                "",
                "必ず以下のJSON形式で返してください：",
                "[",
                "  {",
                "    \"title\": \"① 通常の商品紹介\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                f"    \"title\": \"② 『{post_date}』のモーメントに合わせた投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                "    \"title\": \"③ エンゲージメントを高める投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                "    \"title\": \"④ 直近のキャンペーンに関連した投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                "    \"title\": \"⑤ ユニークで工夫を効かせた投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  },",
                "  {",
                "    \"title\": \"⑥ 自由投稿\",",
                "    \"content\": \"投稿文案...\"",
                "  }",
                "]"
            ])
            
            prompt = "\n".join(prompt_parts)
            
            payload = {
                "messages": [
                    {"role": "system", "content": "あなたはプロのXコンテンツクリエーターです。指定された形式で6種類のX投稿文案をJSON形式で生成してください。必ずJSON形式で返答してください。"},
                    {"role": "user", "content": prompt}
                ],
                "model": "grok-beta",
                "stream": False,
                "temperature": 0.8,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            response_text = response.json()["choices"][0]["message"]["content"].strip()
            
            # JSONの抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
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

def validate_x_url(url: str) -> bool:
    """XのURLかどうかをチェック"""
    if not validate_url(url):
        return False
    parsed = urlparse(url)
    return parsed.netloc.lower() in ['twitter.com', 'x.com', 'www.twitter.com', 'www.x.com']

def main():
    # メインヘッダー
    st.markdown('''
    <div class="hero-section">
        <div class="hero-content">
            <h1 class="hero-title">𝕏 投稿ジェネレーター AI</h1>
            <p class="hero-subtitle">🤖 Grok AIがあなたのXアカウントの雰囲気に合わせて、魅力的な投稿を複数パターン作成します</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # セッション状態の初期化
    if 'analyzed_tone' not in st.session_state:
        st.session_state.analyzed_tone = None
    if 'generated_posts' not in st.session_state:
        st.session_state.generated_posts = None
    if 'loading' not in st.session_state:
        st.session_state.loading = False
    
    # 中央寄せの入力フォーム
    st.markdown('<div class="centered-container">', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        st.markdown("### 📝 基本情報を入力してください")
        
        # 中央寄せのための列配置
        col_left, col_center, col_right = st.columns([1, 3, 1])
        
        with col_center:
            sns_url = st.text_input(
                "🔗 XアカウントURL *",
                placeholder="例: https://x.com/PAPICO_JPN",
                help="分析したいXアカウントのURLを入力してください"
            )
            
            # 2列レイアウト
            date_col, company_col = st.columns([1, 2])
            
            with date_col:
                selected_date = st.date_input(
                    "📅 投稿予定日 *",
                    min_value=date.today(),
                    help="投稿を予定している日付を選択してください"
                )
            
            with company_col:
                company_url = st.text_input(
                    "🏢 企業サイトURL（任意）",
                    placeholder="例: https://jp.glico.com/ice/papico/products.html",
                    help="商品情報を参照する企業サイトのURLを入力してください"
                )
            
            user_request = st.text_area(
                "💡 追加の要望（任意）",
                placeholder="特別な要望があれば入力してください（キャンペーン情報、トーンの調整など）",
                height=100
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 生成ボタン（中央寄せ）
    st.markdown('<div class="generate-section">', unsafe_allow_html=True)
    
    button_col1, button_col2, button_col3 = st.columns([1, 2, 1])
    with button_col2:
        if st.button("✨ X投稿を生成する", type="primary", use_container_width=True):
            # バリデーション
            if not sns_url:
                st.error("XアカウントのURLを入力してください。")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            if not validate_x_url(sns_url):
                st.error("有効なX（旧Twitter）のURLを入力してください。例: https://x.com/account")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            if company_url and not validate_url(company_url):
                st.error("企業サイトURLが有効ではありません。")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            # 生成処理
            try:
                grok_service = GrokService(grok_api_key)
                
                with st.spinner('🤖 Grok AIが投稿を生成中...'):
                    # Step 1: トーン＆マナー分析
                    st.info("🔍 トーン＆マナーを分析中...")
                    
                    analyzed_tone = grok_service.analyze_tone(sns_url, company_url)
                    st.session_state.analyzed_tone = analyzed_tone
                    
                    # Step 2: 投稿生成
                    st.info("📝 X投稿文案を生成中...")
                    
                    post_date = selected_date.strftime('%Y/%m/%d')
                    generated_posts = grok_service.generate_posts(
                        sns_url, company_url, post_date, analyzed_tone, user_request
                    )
                    st.session_state.generated_posts = generated_posts
                    
                    st.success("✅ X投稿の生成が完了しました！")
                    
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 結果表示
    if st.session_state.analyzed_tone:
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        st.markdown("### 🎯 認識されたトーン＆マナー")
        st.markdown(f'''
        <div class="tone-card">
            <div class="tone-header">
                <span class="tone-icon">🤖</span>
                <span class="tone-title">Grok AI分析結果</span>
            </div>
            <div class="tone-content">
                {st.session_state.analyzed_tone}
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    if st.session_state.generated_posts:
        st.markdown("### 🐦 生成されたX投稿文案")
        
        for i, post in enumerate(st.session_state.generated_posts):
            # ユニークなIDを生成
            post_id = f"post_{i}_{uuid.uuid4().hex[:8]}"
            
            # 文字数カウント
            char_count = len(post["content"])
            char_color = "green" if char_count <= 280 else "red"
            
            st.markdown(f'''
            <div class="post-card">
                <div class="post-header">
                    <h4 class="post-title">{post['title']}</h4>
                    <div class="post-actions">
                        <span class="char-count" style="color: {char_color};">{char_count}/280文字</span>
                        <button class="copy-button" onclick="copyToClipboard('{post_id}')">
                            <span class="copy-icon">📋</span>
                            <span class="copy-text">コピー</span>
                        </button>
                    </div>
                </div>
                <div class="post-content" id="{post_id}">
                    {post["content"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # JavaScript for copy functionality
    st.markdown('''
    <script>
    function copyToClipboard(elementId) {
        const element = document.getElementById(elementId);
        const text = element.innerText || element.textContent;
        
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(function() {
                showCopySuccess();
            }).catch(function(err) {
                fallbackCopyTextToClipboard(text);
            });
        } else {
            fallbackCopyTextToClipboard(text);
        }
    }
    
    function fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";
        
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showCopySuccess();
        } catch (err) {
            console.error('コピーに失敗しました: ', err);
            alert('コピーに失敗しました。手動でコピーしてください。');
        }
        
        document.body.removeChild(textArea);
    }
    
    function showCopySuccess() {
        // 成功メッセージの表示
        const toast = document.createElement('div');
        toast.className = 'copy-toast';
        toast.innerHTML = '✅ コピーしました！';
        document.body.appendChild(toast);
        
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 2000);
    }
    </script>
    ''', unsafe_allow_html=True)
    
    # フッター
    st.markdown('''
    <div class="footer">
        <p>🤖 Powered by Grok AI - 生成されたコンテンツは必ず内容を確認・調整してからご利用ください</p>
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()