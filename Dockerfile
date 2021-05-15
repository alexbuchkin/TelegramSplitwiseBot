FROM python:3

WORKDIR /usr/src/TelegramSplitwizeBot

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python3", "-m", "bot" ]
