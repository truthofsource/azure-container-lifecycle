mock_provider "azurerm" {}
run "default_off" {
  command = plan
  assert {
    condition     = length(azurerm_container_app_job.example) == 0
    error_message = "The public example must create no job by default."
  }
}
run "manual_and_disabled" {
  command = plan
  variables { enable_example = true }
  assert {
    condition     = azurerm_container_app_job.example[0].replica_retry_limit == 0
    error_message = "Do not add automatic job retries."
  }
  assert {
    condition     = azurerm_container_app_job.example[0].template[0].container[0].env[0].value == "false"
    error_message = "Real worker execution must stay disabled."
  }
  assert {
    condition     = azurerm_container_app_job.example[0].manual_trigger_config[0].parallelism == 1
    error_message = "Keep manual single-execution configuration."
  }
}
run "tag_rejected" {
  command = plan
  variables { image_digest = "latest" }
  expect_failures = [var.image_digest]
}
