# Outputs for Compute Engine VM module

output "external_ip" {
  description = "External IP address of the Airflow VM"
  value       = google_compute_instance.airflow_vm.network_interface[0].access_config[0].nat_ip
}

output "internal_ip" {
  description = "Internal IP address of the Airflow VM"
  value       = google_compute_instance.airflow_vm.network_interface[0].network_ip
}

output "vm_name" {
  description = "Name of the created VM instance"
  value       = google_compute_instance.airflow_vm.name
}