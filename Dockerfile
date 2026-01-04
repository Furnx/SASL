FROM node:25

WORKDIR /var/sasl

COPY . .

RUN npm i

RUN npm run build

EXPOSE 4173

CMD [ "npm","run","preview"]
