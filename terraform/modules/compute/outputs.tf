output "vm_name" {
  description = "Name of the VM instance"
  value       = google_compute_instance.airflow_vm.name
}

output "external_ip" {
  description = "External IP address of the VM"
  value       = google_compute_address.airflow_ip.address
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh debian@${google_compute_address.airflow_ip.address}"
}