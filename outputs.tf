output "function_name" {
  description = "Cloud Function name."
  value       = google_cloudfunctions_function.function.id
}

output "function_region" {
  description = "Cloud Function region."
  value       = google_cloudfunctions_function.function.region
}