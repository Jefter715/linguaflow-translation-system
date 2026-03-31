from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import boto3
import pandas as pd
import uuid
import io
import base64

# ── Config ──────────────────────────────────────────────────────────────
AWS_REGION = "us-east-1"
INPUT_BUCKET = "linguaflow-input-bucket"
OUTPUT_BUCKET = "linguaflow-responses-bucket"

translate_client = boto3.client("translate", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)

app = FastAPI(title="LinguaFlow API", version="1.0")


# ── Pydantic Models ──────────────────────────────────────────────────────
class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str


class BatchTranslateRequest(BaseModel):
    filename: str  # Original filename (used for S3 key)
    file_content_base64: str  # Base64 encoded file content
    source_lang: str
    target_lang: str


# ── Health Check (CRITICAL for ALB) ──────────────────────────────────────
@app.get("/")
def health_check():
    return {"status": "healthy"}


# ── Single Text Translation ──────────────────────────────────────────────
@app.post("/translate")
async def translate_text(request: TranslateRequest):
    if request.source_lang == request.target_lang:
        return JSONResponse(
            {"error": "Source and target languages must differ"},
            status_code=400
        )

    try:
        resp = translate_client.translate_text(
            Text=request.text,
            SourceLanguageCode=request.source_lang,
            TargetLanguageCode=request.target_lang
        )

        return {"original": request.text, "translated": resp.get("TranslatedText")}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Batch File Translation ──────────────────────────────────────────────
@app.post("/batch")
async def batch_translate(request: BatchTranslateRequest):
    try:
        # Decode file content
        file_bytes = base64.b64decode(request.file_content_base64)
        file_buffer = io.BytesIO(file_bytes)

        # Upload input file to S3
        input_key = f"input/{uuid.uuid4()}_{request.filename}"
        s3_client.put_object(Bucket=INPUT_BUCKET, Key=input_key, Body=file_bytes)

        translated_rows = []

        # ── CSV Handling ────────────────────────────────────────────────
        if request.filename.lower().endswith(".csv"):
            df = pd.read_csv(file_buffer)

            if "text" not in df.columns:
                raise HTTPException(status_code=400, detail="CSV must have a column named 'text'")

            for _, row in df.iterrows():
                try:
                    translated = translate_client.translate_text(
                        Text=str(row["text"]),
                        SourceLanguageCode=request.source_lang,
                        TargetLanguageCode=request.target_lang
                    )["TranslatedText"]
                except Exception as e:
                    translated = f"[ERROR] {str(e)}"

                translated_rows.append(translated)

            df["translated"] = translated_rows
            output_buffer = io.StringIO()
            df.to_csv(output_buffer, index=False)
            output_bytes = output_buffer.getvalue().encode("utf-8")

        # ── TXT Handling ────────────────────────────────────────────────
        else:
            lines = file_bytes.decode("utf-8").splitlines()
            for line in lines:
                try:
                    translated = translate_client.translate_text(
                        Text=line,
                        SourceLanguageCode=request.source_lang,
                        TargetLanguageCode=request.target_lang
                    )["TranslatedText"]
                except Exception as e:
                    translated = f"[ERROR] {str(e)}"

                translated_rows.append(translated)

            output_bytes = "\n".join(translated_rows).encode("utf-8")

        # Upload translated file to S3
        output_key = f"output/{uuid.uuid4()}_{request.filename}"
        s3_client.put_object(Bucket=OUTPUT_BUCKET, Key=output_key, Body=output_bytes)

        return {
            "s3_input_key": input_key,
            "s3_output_key": output_key,
            "rows_translated": len(translated_rows)
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── List Translation History ─────────────────────────────────────────────
@app.get("/history")
async def list_history(bucket: str = OUTPUT_BUCKET, prefix: str = "output/"):
    try:
        resp = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        files = [obj["Key"] for obj in resp.get("Contents", [])]
        return {"files": files}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)