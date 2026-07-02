{{/*
Expand the name of the chart.
*/}}
{{- define "sports-scores-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "sports-scores-api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "sports-scores-api.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "sports-scores-api.labels" -}}
helm.sh/chart: {{ include "sports-scores-api.chart" . }}
{{ include "sports-scores-api.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.labels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "sports-scores-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sports-scores-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use.
*/}}
{{- define "sports-scores-api.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "sports-scores-api.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the config map name.
*/}}
{{- define "sports-scores-api.configMapName" -}}
{{- printf "%s-config" (include "sports-scores-api.fullname" .) }}
{{- end }}

{{/*
Create the secret name.
*/}}
{{- define "sports-scores-api.secretName" -}}
{{- printf "%s-secret" (include "sports-scores-api.fullname" .) }}
{{- end }}