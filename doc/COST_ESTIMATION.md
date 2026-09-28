# 💰 RAG Quiz Generator Backend - Cost Estimation & Pricing Model

## 1. Executive Summary

This document provides a comprehensive cost estimation for the **RAG Quiz Generator Backend** powered by FastAPI, LlamaIndex, `sentence-transformers/all-MiniLM-L6-v2`, and Google Gemini 2.5 Flash LLM.

Thanks to the hybrid architecture (Local CPU-based Embeddings + Cloud Serverless LLM), the system achieves **near-zero operational costs** for development and small-to-medium production workloads, with transparent and predictable scaling costs.

---

## 2. Architectural Cost Breakdown

| Component | Technology | Cost Model | Estimated Unit Cost |
| :--- | :--- | :--- | :--- |
| **LLM Reasoning & Generation** | Google Gemini 2.5 Flash | Pay-as-you-go / Free Tier | $0.075 / 1M input tokens<br/>$0.300 / 1M output tokens |
| **Embeddings Generation** | `sentence-transformers/all-MiniLM-L6-v2` | Self-hosted (In-process CPU) | **$0.00 (100% Free, Unlimited)** |
| **Vector Index & Retrieval** | LlamaIndex VectorStoreIndex + Disk Cache | Local Filesystem (`storage/`) | **$0.00 (100% Free)** |
| **API Framework & Runtime** | FastAPI + Uvicorn + Python 3.11 | Self-hosted / VPS / Serverless | Minimal to Free Tier |

---

## 3. Google Gemini Pricing Tiers

### 3.1. Free Tier (Zero-Cost Operation)
Google AI Studio offers a free tier for Gemini 2.5 Flash:
- **Rate Limit:** 15 Requests Per Minute (RPM)
- **Token Throughput:** 1,000,000 Tokens Per Minute (TPM)
- **Daily Request Limit:** **1,500 Requests Per Day (RPD)**

#### Free Capacity Calculations:
- If each request generates **5 MCQs**:
  - **Daily Free Output:** $1,500 \times 5 = \mathbf{7,500\text{ questions / day}}$
  - **Monthly Free Output:** $7,500 \times 30 = \mathbf{225,000\text{ questions / month}}$
- **Cost:** **$0.00 / month (₹0)**

---

### 3.2. Paid Tier (Pay-As-You-Go Scale)
When exceeding the 1,500 daily requests threshold or for high-concurrency production deployments:

| Metric | Google Gemini 2.5 Flash Rate |
| :--- | :--- |
| **Input Tokens** (Prompt + Retrieved PDF Chunks) | **$0.075 per 1,000,000 tokens** (~₹6.25 / 1M tokens) |
| **Output Tokens** (Generated Quiz JSON) | **$0.300 per 1,000,000 tokens** (~₹25.00 / 1M tokens) |

---

## 4. Token Economics & Mathematical Formulas

### 4.1. Average Payload Token Profiles

#### A. Input Tokens per Quiz Request:
- **System & Formatting Instructions:** ~200 tokens
- **Retrieved PDF Context (Top 3 Chunks, 1024-token window):** ~1,500 tokens
- **Total Input Tokens ($T_{in}$):** **~1,700 tokens**

#### B. Output Tokens per Quiz Request (5 MCQs in strict JSON format):
- Question, 4 Options, Correct Answer, Explanation: ~100 tokens per MCQ
- JSON Formatting Overhead: ~50 tokens
- **Total Output Tokens ($T_{out}$):** **~500 tokens**

---

### 4.2. Unit Cost Formula

$$\text{Cost per Quiz Request} = \left(\frac{T_{in}}{10^6} \times P_{in}\right) + \left(\frac{T_{out}}{10^6} \times P_{out}\right)$$

Where:
- $T_{in} = 1,700$
- $P_{in} = \$0.075$
- $T_{out} = 500$
- $P_{out} = \$0.300$

$$\text{Input Cost} = \frac{1,700}{1,000,000} \times \$0.075 = \$0.0001275$$
$$\text{Output Cost} = \frac{500}{1,000,000} \times \$0.300 = \$0.0001500$$
$$\mathbf{\text{Total Cost per Quiz (5 MCQs)}} = \$0.0001275 + \$0.0001500 = \mathbf{\$0.0002775}\text{ (approx. ₹0.023)}$$

#### Cost per Individual Question:
$$\mathbf{\text{Cost per 1 Question}} = \frac{\$0.0002775}{5} = \mathbf{\$0.0000555}\text{ (approx. ₹0.0046 / 0.46 paise)}$$

---

## 5. Cost Scaling Projections Matrix

*(Assuming standard 5-question quizzes generated via Gemini 2.5 Flash Pay-as-you-go)*

| Questions Generated | Quizzes Requested | Input Tokens | Output Tokens | Total Cost (USD) | Total Cost (INR ₹)* |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **100** | 20 | 34,000 | 10,000 | **$0.0055** | **₹0.46** |
| **500** | 100 | 170,000 | 50,000 | **$0.0278** | **₹2.31** |
| **1,000** | 200 | 340,000 | 100,000 | **$0.0555** | **₹4.61** |
| **5,000** | 1,000 | 1,700,000 | 500,000 | **$0.2775** | **₹23.03** |
| **10,000** | 2,000 | 3,400,000 | 1,000,000 | **$0.5550** | **₹46.07** |
| **50,000** | 10,000 | 17,000,000 | 5,000,000 | **$2.7750** | **₹230.33** |
| **100,000 (1 Lakh)** | 20,000 | 34,000,000 | 10,000,000 | **$5.5500** | **₹460.65** |
| **500,000 (5 Lakhs)** | 100,000 | 170,000,000 | 50,000,000 | **$27.7500** | **₹2,303.25** |
| **1,000,000 (1 Million)** | 200,000 | 340,000,000 | 100,000,000 | **$55.5000** | **₹4,606.50** |

*\*Assumed exchange rate: 1 USD ≈ 83 INR.*

---

## 6. Hosting & Infrastructure Costs

| Deployment Tier | Recommended Platform | Specs | Monthly Cost |
| :--- | :--- | :--- | :--- |
| **Local / Dev** | Local PC / Workstation | Standard CPU, 4GB+ RAM | **$0.00** |
| **Hobby / Prototype** | Render / Railway / Hugging Face Spaces | 0.5 - 1 CPU, 512MB RAM | **$0.00 - $5.00** |
| **Small Production** | DigitalOcean Droplet / Hetzner Cloud | 2 vCPU, 2GB - 4GB RAM, 40GB SSD | **$4.00 - $6.00 / month** |
| **Enterprise Production** | AWS EC2 (t4g.small / t3.medium) | 2 vCPU, 4GB RAM + Auto-scaling | **$15.00 - $30.00 / month** |

---

## 7. Cost Optimization Strategies Implemented

1. **Local CPU Embedding Engine:**
   - Switched from heavy cloud-billed embeddings to local `sentence-transformers/all-MiniLM-L6-v2`.
   - **Savings:** Saved 100% of embedding API costs ($0.00 per document chunk).

2. **Persistent Disk Vector Storage (`storage/`):**
   - Documents are embedded once and cached to disk. Subsequent queries reuse the persistent index without re-calculating embeddings.
   - **Savings:** Zero redundant computation or reprocessing costs.

3. **Top-K Chunk Filtering:**
   - Restricting similarity search to `similarity_top_k=3` limits input context to ~1,500 tokens per request, preventing bloated prompt token billing.

4. **Model Efficiency:**
   - Utilizing `gemini-2.5-flash` rather than `gemini-pro` provides an **80-90% cost reduction** with superior latency and structured JSON accuracy.
