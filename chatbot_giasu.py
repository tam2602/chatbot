import os
import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import mic_recorder

# --- 1. THIẾT LẬP API KEY VÀ CLIENT ---

# Lấy API Key từ biến môi trường (Environment Variable)
# LƯU Ý: Vui lòng thay thế chuỗi "A" bằng API Key hợp lệ của bạn.
API_KEY = ""
if API_KEY == "A":
    API_KEY = "YOUR_VALID_API_KEY_HERE"  # Thay đổi dòng này!

if not API_KEY or API_KEY == "YOUR_VALID_API_KEY_HERE":
    st.error("Lỗi: Vui lòng thay thế 'YOUR_VALID_API_KEY_HERE' trong code bằng API Key hợp lệ của bạn.")
    st.stop()

# Khởi tạo client
try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"Lỗi khởi tạo client: {e}")
    st.stop()

# --- 2. PROMPT CỐT LÕI (SYSTEM INSTRUCTION) ---

SYSTEM_INSTRUCTION = (
    "Bạn là 'LinguaMaster', một Gia sư Ngoại ngữ AI toàn diện, chuyên dạy tiếng Anh. "
    "Mục tiêu của bạn là cung cấp trải nghiệm học tập cá nhân hóa, sinh động và thực tế. "
    "Mức độ hội thoại ban đầu là A2 (Sơ cấp), và sẽ được điều chỉnh linh hoạt. "
    "Bạn phải tuân thủ nghiêm ngặt định dạng phản hồi và các chức năng sau: "

    "1. **Phản hồi Trò chuyện (Tiếng Anh):** Trả lời tự nhiên, duy trì ngữ cảnh. Đặt câu hỏi hoặc đưa ra tình huống phù hợp với mức độ hiện tại của học viên. "
    "2. **Phân tích Học tập và Đề xuất (Tiếng Việt):** "
    "   - **Phân loại Trình độ:** Đánh giá nhanh cấp độ hiện tại của học viên (A1, A2, B1, B2...) dựa trên câu cuối cùng. "
    "   - **Sửa Lỗi Ngữ pháp/Diễn đạt:** Sửa lỗi rõ ràng và cung cấp câu diễn đạt tự nhiên hơn (Native speaker usage). "
    "   - **Gợi Ý Từ vựng/Chủ đề:** Đề xuất 1-2 từ vựng mới hoặc chủ đề luyện tập phù hợp với lỗi sai/chủ đề hiện tại. "
    "3. **Chế độ Luyện tập Đặc biệt (Activation):** Nếu học viên yêu cầu các chế độ như 'Luyện Phát âm' / 'Luyện Nghe', hãy chuyển sang chế độ đó. "
    "4. **LƯU Ý BẮT BUỘC:** Luôn sử dụng ngôn ngữ mục tiêu (Tiếng Anh) trong hội thoại và TIẾNG VIỆT trong phần Phân tích/Đề xuất."
)


# --- 3. HÀM GỌI API VÀ XỬ LÝ LỊCH SỬ HỘI THOẠI (STABLE METHOD) ---

def get_gemini_response(history, current_prompt):
    """Gửi toàn bộ lịch sử và prompt mới tới Gemini (Phương pháp ổn định)."""

    # Chuẩn bị dữ liệu lịch sử theo định dạng Content của Gemini API
    contents = []

    # Thêm SYSTEM_INSTRUCTION vào đầu để đảm bảo vai trò gia sư
    # SỬA LỖI: Thay thế from_text(...) bằng Part(text=...)
    contents.append(types.Content(role="user", parts=[types.Part(text=SYSTEM_INSTRUCTION)]))
    contents.append(types.Content(role="model", parts=[types.Part(
        text="OK. I understand my role and will begin the conversation now. Hello! What would you like to talk about today?")]))

    # Chuyển lịch sử Streamlit sang định dạng API
    for message in history:
        # Bỏ qua tin nhắn chào đầu tiên và instruction (đã được chèn ở trên)
        if message["content"].startswith("Hello! I am LinguaMaster.") or message["content"].startswith(
                "OK. I understand my role."):
            continue

        # Thêm tin nhắn cũ vào lịch sử
        # SỬA LỖI: Thay thế from_text(...) bằng Part(text=...)
        contents.append(types.Content(role=message["role"], parts=[types.Part(text=message["content"])]))

    # Thêm prompt hiện tại của người dùng
    # SỬA LỖI: Thay thế from_text(...) bằng Part(text=...)
    contents.append(types.Content(role="user", parts=[types.Part(text=current_prompt)]))

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        return response.text
    except Exception as e:
        # Bắt lỗi 503/Mạng và trả về thông báo thân thiện
        print(f"\n--- LỖI API CHI TIẾT TRONG TERMINAL ---")
        print(e)
        print("---------------------------------------")
        return f"**LỖI KẾT NỐI/DỊCH VỤ (UNAVAILABLE):** Rất tiếc, máy chủ Gemini đang quá tải hoặc lỗi kết nối. Vui lòng chờ vài giây và thử lại câu hỏi cuối cùng của bạn."


# --- 4. KHỞI TẠO VÀ QUẢN LÝ LỊCH SỬ CHAT (SESSION STATE) ---

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "model", "content": "Hello! I am LinguaMaster. What would you like to practice today?"}
    ]

# --- 5. THIẾT LẬP GIAO DIỆN STREAMLIT ---

st.set_page_config(page_title="🤖 LinguaMaster - Gia sư Tiếng Anh AI",
                   layout="wide")  # Đổi sang wide để mic recorder có không gian
st.title("🤖 LinguaMaster - Gia sư Tiếng Anh AI")
st.caption("Hãy bắt đầu trò chuyện bằng tiếng Anh! Nhấn F5 nếu cần tải lại.")


# Nút để bắt đầu cuộc trò chuyện mới
def new_chat_stable():
    st.session_state["messages"] = [
        {"role": "model", "content": "Hello! I am LinguaMaster. What would you like to practice today?"}
    ]


st.sidebar.button("➕ Bắt đầu Chủ đề/Cuộc trò chuyện Mới", on_click=new_chat_stable)

# Hiển thị lịch sử chat
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. XỬ LÝ ĐẦU VÀO NGƯỜI DÙNG (TEXT & VOICE) ---

st.sidebar.markdown("---")
st.sidebar.markdown("## 🎙️ Tương tác Giọng nói (STT)")
st.sidebar.warning("Hãy đảm bảo trình duyệt đã cấp quyền truy cập Microphone!")

# Sử dụng mic_recorder để ghi âm (STT) - Đã bỏ tham số 'just_released'
mic_result = mic_recorder(
    start_prompt="Bắt đầu Ghi âm",
    stop_prompt="Dừng Ghi âm",
    use_container_width=True,
    format="wav",
    key='mic_recorder'
)

# Khai báo biến đầu vào
prompt = None

# Nếu có văn bản từ bộ ghi âm
if mic_result and 'text' in mic_result and mic_result['text']:
    prompt = mic_result['text']
    # Dùng st.empty() để tạm hiển thị text trước khi xử lý
    st.info(f"🎤 Văn bản nhận được: {prompt}")

# Kiểm tra ô chat văn bản (luôn đặt ở cuối để nó được kiểm tra lần cuối)
if not prompt:
    prompt = st.chat_input("Hoặc nhập câu tiếng Anh của bạn tại đây...")

# --- 7. XỬ LÝ TIN NHẮN CUỐI CÙNG ---

# Khối này chỉ chạy khi có một 'prompt' mới (từ giọng nói hoặc văn bản)
if prompt:
    # 1. Hiển thị tin nhắn người dùng
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Gửi prompt đến Gemini API
    with st.spinner("LinguaMaster đang suy nghĩ..."):
        full_response = get_gemini_response(st.session_state["messages"], prompt)

    # 3. Hiển thị phản hồi của Gemini
    with st.chat_message("assistant"):
        st.markdown(full_response)

    # 4. Lưu phản hồi vào lịch sử chat
    st.session_state["messages"].append({"role": "model", "content": full_response})