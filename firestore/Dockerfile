FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:alpine
RUN apk --update add openjdk11-jre
ENTRYPOINT ["gcloud", "emulators", "firestore", "start", "--host-port=0.0.0.0:8080", "--quiet"]
