FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY . .
RUN CGO_ENABLED=0 go build -o /policy-gate .

FROM gcr.io/distroless/static-debian12
COPY --from=build /policy-gate /policy-gate
EXPOSE 8091
ENTRYPOINT ["/policy-gate"]
