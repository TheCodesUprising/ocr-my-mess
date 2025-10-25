FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3 python3-pip libxcb1

WORKDIR /app

RUN pip install pytest pypdf --break-system-packages

COPY dist/ocr-my-mess .
COPY tests .

ENV OCR_MY_MESS_EXECUTABLE=/app/ocr-my-mess

CMD ["pytest", "-vvv", "test_end_to_end.py"]
