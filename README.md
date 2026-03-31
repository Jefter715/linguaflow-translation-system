# 🌍 LinguaFlow – AI Translation System

## 🚀 Overview
LinguaFlow is a cloud-based AI-powered translation system designed to provide real-time and batch multilingual translation using scalable cloud infrastructure.

This project demonstrates the integration of:
- Cloud computing (AWS)
- Containerization (Docker)
- Backend APIs (FastAPI)
- Infrastructure as Code (Terraform)
- Interactive UI (Streamlit)

---

## 🎯 Problem Statement
In global communication, language barriers limit accessibility and efficiency in:
- Customer support
- International business
- Content localization

LinguaFlow solves this by providing a scalable, API-driven translation system.

---

## 🏗️ Architecture

### 🔹 System Flow
1. User interacts via Streamlit UI
2. Request sent to API Gateway
4. API Gateway routes request through an Aplication Load balancer to FastAPI backend (Docker container on ECS)
5. FastAPI processes translation
6. Response returned to user

---

## ⚙️ Tech Stack

### Backend
- FastAPI
- Python

### Frontend
- Streamlit

### Cloud & DevOps
- AWS API Gateway
- AWS ECS (Fargate)
- Docker
- Terraform

---

## 📦 Features

-  Real-time text translation
-  CSV batch translation (Direct API mode)
-  Scalable cloud architecture
-  Modular infrastructure (Terraform)

---

## 🔮 Future Improvements

-  SQS + Lambda for async batch processing
-  Monitoring with CloudWatch
-  Caching with Redis
-  Authentication system
-  Multi-language output

---

## 🧪 How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app/app.py```


 API Test

curl -X POST https://<your-api-endpoint>/translate \
-H "Content-Type: application/json" \
-d '{"text":"Hello world","source_lang":"en","target_lang":"fr"}'
