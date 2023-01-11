terraform {
  # backend "gcs" {
  #   bucket  = "icici-bucket"
  #   prefix  = "terraform/state"
  # }
}

provider "google" {
 credentials = file("${var.credentials}")
 project     = var.gcp_project
 region      = var.region
}



resource "google_storage_bucket" "log-bucket" {
  name = var.bucket_name
  force_destroy = true
}

resource "google_storage_bucket_object" "archive" {
  name   = "index.zip"
  bucket = google_storage_bucket.log-bucket.name
  source = "index.zip"
}


resource "google_pubsub_topic" "example" {
  name = var.topic_name

}

# Our sink; this logs all activity related to our "my-logged-instance" instance
resource "google_logging_project_sink" "instance-sink" {
  name        = "${var.topic_name}-sink"
  destination = "pubsub.googleapis.com/${google_pubsub_topic.example.id}"
  filter      = "protoPayload.methodName=(\"beta.compute.instances.insert\" OR \"storage.buckets.create\" OR \"beta.compute.disks.insert\" OR \"beta.compute.disks.createSnapshot\" OR \"v1.compute.disks.createSnapshot\" OR \"v1.compute.images.insert\" OR \"cloudsql.instances.create\" OR \"datasetservice.insert\" OR \"google.container.v1beta1.ClusterManager.CreateCluster\" OR \"v1.compute.instances.insert\")"
  unique_writer_identity = true
  depends_on = [google_pubsub_topic.example]
}

# Because our sink uses a unique_writer, we must grant that writer access to the bucket.
resource "google_project_iam_binding" "log-writer" {
  role = "roles/pubsub.publisher"

  members = [
    google_logging_project_sink.instance-sink.writer_identity
  ]
  depends_on = [google_logging_project_sink.instance-sink]
}


resource "google_service_account" "sa" {
  account_id   = "${var.gcp_project}-disk"
  display_name = var.sa
}


resource "google_project_iam_binding" "cfsa-editor-role" {
  role    = "roles/editor"
    members = [
        "serviceAccount:${google_service_account.sa.email}"
    ]
}


resource "google_cloudfunctions_function" "function" {
  name        = "terraform-test"
  description = "By Terraform function"
  runtime     = "python37"
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.log-bucket.name
  source_archive_object = google_storage_bucket_object.archive.name
  service_account_email = google_service_account.sa.email
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource = "projects/${var.gcp_project}/topics/${var.topic_name}"
  }
  timeout               = 300
  entry_point           = "hello_pubsub"
  labels = {
    managedby = "cloudcover",createdby ="terraform"
  }

  environment_variables = {
    project = var.gcp_project
    webhook = var.webhook
  }
  depends_on = [google_pubsub_topic.example]
}
