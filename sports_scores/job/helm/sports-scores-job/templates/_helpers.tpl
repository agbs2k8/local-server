{{/*
Expand the name of the chart.
*/}}
{{- define "sports-scores-job.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "sports-scores-job.fullname" -}}
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
{{- define "sports-scores-job.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "sports-scores-job.labels" -}}
helm.sh/chart: {{ include "sports-scores-job.chart" . }}
{{ include "sports-scores-job.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "sports-scores-job.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sports-scores-job.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "sports-scores-job.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "sports-scores-job.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create secret name
*/}}
{{- define "sports-scores-job.secretName" -}}
{{- printf "%s-secret" (include "sports-scores-job.fullname" .) }}
{{- end }}

{{/*
Create configmap name
*/}}
{{- define "sports-scores-job.configMapName" -}}
{{- printf "%s-config" (include "sports-scores-job.fullname" .) }}
{{- end }}