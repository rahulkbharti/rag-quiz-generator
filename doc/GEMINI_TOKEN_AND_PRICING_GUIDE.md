# 🪙 Google Gemini Token & Pricing Master Guide
### (टोकन क्या होता है, कितना पैसा लगता है और कैसे पता करें)

---

## 1. टोकन (Token) क्या होता है?

AI models (jaise Google Gemini, ChatGPT) insaan ki tarah poore shabd (words) nahi padhte, balki text ko chhote-chhote tukdon me todte hain jinhe **Tokens** kaha jata hai.

### Thumb Rule for Tokens:
* **English Text:** 1 Token $\approx$ lagbhag **0.75 Words** (yaani 4 Characters).
  * Example: `"School ERP"` = **2 Tokens**.
  * Example: `"Attendance upload error"` = **3 Tokens**.
  * **100 English Words** $\approx$ **~130 se 140 Tokens**.
* **Hindi / Hinglish Text:** Hindi aur mixed Hinglish me tokens thode zyada bante hain kyunki script complex hoti hai.
  * **1 Word** $\approx$ **1.5 se 2 Tokens**.
  * Example: `"Fee receipt format kaise badlein?"` $\approx$ **6–8 Tokens**.

### Quick Conversion Scale:

| Text Type | Word Count | Approximate Tokens |
| :--- | :--- | :--- |
| **Short Support Query** | 10 – 15 words | **~20 – 30 tokens** |
| **1 Detailed Paragraph** | 100 words | **~130 – 150 tokens** |
| **1 Page A4 Document** | 500 words | **~650 – 750 tokens** |
| **10-Page ERP Manual** | 5,000 words | **~6,500 – 7,500 tokens** |

---

## 2. Google AI Billing Kaise Kaam Karti Hai?

Google AI Studio hamesha pricing **"Per 1 Million (10 Lakh) Tokens"** me measure karta hai.

Isme 2 alag-alag billing rates hote hain:

```
┌──────────────────────────────────────────────────────────────┐
│                      TOTAL QUERY TOKENS                      │
├──────────────────────────────┬───────────────────────────────┤
│        INPUT TOKENS          │        OUTPUT TOKENS          │
│   (Prompt + User Query +     │     (AI ka generate kiya      │
│        RAG Context)          │         hua Jawab)            │
│                              │                               │
│       Rate: Sasta            │     Rate: 3x - 4x Mehanga     │
│   ($0.075 / 10 Lakh tokens)  │   ($0.300 / 10 Lakh tokens)   │
└──────────────────────────────┴───────────────────────────────┘
```

1. **Input Tokens ($T_{in}$):** Jo data hum Google ko bhejte hain (User ka sawal + System Prompt + Manual ke paragraphs).
2. **Output Tokens ($T_{out}$):** Jo answer Gemini generate karke wapas bhejta hai. Output token generate karne me zyada computing power lagti hai, isliye ye input se 3x–4x mehanga hota hai.

---

## 3. Gemini Models ka Official Price Chart

*(Rates from Google AI Studio official pricing; 1 USD $\approx$ ₹86 INR assumed + 18% GST buffer)*

| Model | Recommended Use Case | Input Rate (Per 10 Lakh Tokens) | Output Rate (Per 10 Lakh Tokens) | 1 Query ka Approx Kharcha |
| :--- | :--- | :--- | :--- | :--- |
| **Gemini 1.5 / 2.0 / 2.5 Flash** *(Best for Support Bot & Quiz)* | Fast response (<2s), high volume, routine ERP how-to | **$0.075** (~₹6.45) | **$0.300** (~₹25.80) | **~₹0.02 (2 se 2.5 paise)** |
| **Gemini Flash-Lite** | Ultra low-cost, classification, summarization | **$0.075 – $0.10** (~₹7.50) | **$0.300 – $0.40** (~₹30.00) | **~₹0.02 (2 paise)** |
| **Gemini Pro (3.1 / 1.5 Pro)** | Complex reasoning, deep code debugging | **$1.25 – $2.00** (~₹120 – ₹172) | **$5.00 – $10.00** (~₹430 – ₹860) | **~₹0.35 – ₹0.60 (35 se 60 paise)** |
| **Text Embedding 004** *(Cloud Embeddings)* | Vector search (agar local embedder na use karein) | **$0.00** (Free up to limit) / **$0.02** | N/A (Sirf input hota hai) | **Negligible** |

---

## 4. Kitne Token ka Kitna Paisa Lagega? (Exact Mathematics)

### 4.1. Unit Calculation (Gemini Flash Model)

$$\text{1 Input Token Cost} = \frac{\$0.075}{1,000,000} = \$0.000000075 \approx \mathbf{₹0.00000645}\text{ (0.0006 paise)}$$
$$\text{1 Output Token Cost} = \frac{\$0.300}{1,000,000} = \$0.000000300 \approx \mathbf{₹0.00002580}\text{ (0.0026 paise)}$$

---

### 4.2. Token Volume vs. Kharcha Table (INR ₹)

| Token Volume | Input Cost (Prompt) | Output Cost (AI Answer) | Total (Approx. INR) |
| :--- | :--- | :--- | :--- |
| **1,000 Tokens** | ₹0.0065 | ₹0.0258 | **~₹0.03 (3 paise)** |
| **10,000 Tokens** | ₹0.065 | ₹0.258 | **~₹0.32 (32 paise)** |
| **100,000 Tokens (1 Lakh)** | ₹0.65 | ₹2.58 | **~₹3.20 (3 rupaye 20 paise)** |
| **1,000,000 Tokens (10 Lakh)** | ₹6.45 | ₹25.80 | **~₹32.00 (32 rupaye)** |

---

### 4.3. Real-World Query Example (ERP Support Chatbot)

Maan lijiye Accountant ne poochha: *"Class 5 ka fee concession kaise apply karein?"*

1. **Input Breakdown:**
   * User ka sawal: ~50 tokens
   * System Prompt (Rules): ~400 tokens
   * ERP Manual Context (Top 2 chunks): ~1,200 tokens
   * Conversation history: ~150 tokens
   * **Total Input:** **1,800 tokens**
   * $\text{Input Cost} = \frac{1,800}{1,000,000} \times \$0.075 \times 86 = \mathbf{₹0.0116}$ (1.1 paise)

2. **Output Breakdown:**
   * AI ne 4 steps ka step-by-step solution generate kiya: **~250 tokens**
   * $\text{Output Cost} = \frac{250}{1,000,000} \times \$0.300 \times 86 = \mathbf{₹0.0064}$ (0.64 paise)

3. **Total Ek Query Ka Bill:**
   $$\mathbf{₹0.0116 + ₹0.0064 = ₹0.018}\text{ (Sirf 1.8 Paise!)}$$

---

### 4.4. "Rupaye me kitna kaam hoga?" (Rule of Thumb)

* **₹1 me:** Lagbhag **45 se 55 support answers** mil sakte hain.
* **₹10 me:** Lagbhag **500 answers**.
* **₹100 me:** Lagbhag **5,000 answers**.
* **₹500 me:** Lagbhag **25,000 answers** (50 schools ka 1 mahine ka support load).

---

## 5. Model ka Charge aur Tokens Kaise Pata Karein? (3 Practical Tarike)

### Tarika 1: Official Google Pricing Page (Direct Source of Truth)
Google har model ka official live price yahan update karta hai:
* 👉 **URL:** [https://ai.google.dev/pricing](https://ai.google.dev/pricing)
* Yahan aap har model ke table me dekh sakte hain:
  - Input price per 1M tokens
  - Output price per 1M tokens
  - Context Caching discounts
  - Free tier limits (RPM, TPM, RPD)

---

### Tarika 2: Google AI Studio Web Playground me Live Counter
Agar aapke paas koi document ya text hai aur aapko dekhna hai isme kitne tokens bante hain:
1. **[aistudio.google.com](https://aistudio.google.com)** par login karein.
2. Prompt window me apna text ya ERP documentation paste karein.
3. Bottom-right corner me live token counter dikhta hai:
   $$\text{Tokens: 1,420 / 1,048,576}$$
4. Isse bina kisi API call ke exact token count pata chal jata hai.

---

### Tarika 3: Python Backend Code me Exact Tokens & Cost Measure Karna

Aap apne FastAPI backend me har query ka live token count aur rupaye me kharcha log kar sakte hain:

```python
import os
from google import genai

# Client initialize karein
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

model_name = "gemini-2.5-flash"
prompt_text = "Class 5 ke fee concession rules aur step-by-step navigation batayein."

# -------------------------------------------------------------
# STEP A: API Call karne se pehle tokens count karna (Free)
# -------------------------------------------------------------
token_info = client.models.count_tokens(
    model=model_name,
    contents=prompt_text,
)
print(f"Estimated Input Tokens: {token_info.total_tokens}")

# -------------------------------------------------------------
# STEP B: Model se response lena
# -------------------------------------------------------------
response = client.models.generate_content(
    model=model_name,
    contents=prompt_text,
)

# -------------------------------------------------------------
# STEP C: Exact Tokens aur Cost Calculate karna
# -------------------------------------------------------------
metadata = response.usage_metadata
input_tokens = metadata.prompt_token_count
output_tokens = metadata.candidates_token_count
total_tokens = metadata.total_token_count

# Official Pricing Rates (Gemini Flash)
USD_TO_INR = 86.0  # Current Dollar to Rupee rate
RATE_INPUT_PER_M = 0.075 * USD_TO_INR   # ₹6.45 per 1M
RATE_OUTPUT_PER_M = 0.300 * USD_TO_INR  # ₹25.80 per 1M

cost_input_inr = (input_tokens / 1_000_000) * RATE_INPUT_PER_M
cost_output_inr = (output_tokens / 1_000_000) * RATE_OUTPUT_PER_M
total_cost_inr = cost_input_inr + cost_output_inr

print(f"--- Token Usage Report ---")
print(f"Input Tokens : {input_tokens} (Cost: ₹{cost_input_inr:.4f})")
print(f"Output Tokens: {output_tokens} (Cost: ₹{cost_output_inr:.4f})")
print(f"Total Tokens : {total_tokens}")
print(f"Total Bill   : ₹{total_cost_inr:.4f} INR (~{total_cost_inr * 100:.2f} paise)")
```

---

## 6. Billing Alerts aur Budget Cap Kaise Lagayein? (Zaruri Safety)

Bina marzi paise katne se bachne ke liye Google Cloud par 2 safety features lagana zaroori hai:

1. **Google Cloud Billing Hard Cap / Budget Alert:**
   * Google Cloud Console par jayein: `console.cloud.google.com/billing`
   * **Budgets & Alerts** menu par click karein.
   * Ek monthly budget banayein (e.g., **₹500 ya ₹1,000**).
   * Alert set karein: 50%, 80%, aur 100% par aapko turant email aa jayega.
2. **API Rate Limiter in Backend:**
   * Apne FastAPI backend par per-user rate limit lagayein (e.g. 1 user maximum 20 queries/minute), taaki koi script chala kar aapka token balance khatam na kar sake.
3. **Max Output Tokens Limit:**
   * API call me `max_output_tokens=400` set karein taaki AI lambe essay generate karke faltu output tokens na kharche.

---

## 7. Frequently Asked Questions (FAQ)

#### Q1: Kya Google AI Studio ke Free Tier me paise katenge?
**Nahi.** Free Tier me credit card charge nahi hota. Limit khatam hone par API `HTTP 429 Too Many Requests` error degi, par paise kabhi nahi katenge.

#### Q2: Paid Tier kab enable karna chahiye?
Jab aap production me 10+ schools ya high-concurrency users ko live service dete hain. Paid tier par data privacy guaranteed hoti hai (Google aapka data models train karne me use nahi karta) aur rate limit 1,000+ RPM ho jati hai.

#### Q3: Agar 100 schools ek saath chatbot use karein to kitna bill aayega?
100 schools agar din me 400 queries (mahine me 12,000 queries) karein, to pure mahine ka Google AI token bill sirf **~₹250 se ₹350** aayega.
