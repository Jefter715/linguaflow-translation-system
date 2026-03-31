resource "aws_s3_bucket" "input" {
  bucket = var.input_bucket_name
}

resource "aws_s3_bucket" "responses" {
  bucket = var.responses_bucket_name
}