{{/*
Create a default fully qualified app name.
*/}}
{{- define "common.fullname" -}}
{{- if .Values.webhook.fullnameOverride }}
{{- .Values.webhook.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default "webhook" .Values.webhook.appNameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create a default app name.
*/}}
{{- define "common.appName" -}}
{{- if .Values.webhook.appNameOverride }}
{{- .Values.webhook.appNameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- .Chart.Name }}
{{- end }}
{{- end }}

{{/*
Return the proper bc sed image name
*/}}
{{- define "common.webImage" -}}
{{- $registryName := .Values.webhook.image.registry -}}
{{- $repositoryName := .Values.webhook.image.repository -}}
{{- if .Values.webhook.image.tag }}
{{- printf "%s/%s:%s" $registryName $repositoryName .Values.webhook.image.tag -}}
{{- else }}
{{- printf "%s/%s:%s" $registryName $repositoryName .Chart.AppVersion -}}
{{- end }}
{{- end -}}
