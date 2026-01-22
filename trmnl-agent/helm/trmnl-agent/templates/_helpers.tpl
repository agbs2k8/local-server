{{/*
Expand the name of the chart.
*/}}
{{- define "trmnl-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "trmnl-agent.fullname" -}}
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
{{- define "trmnl-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "trmnl-agent.labels" -}}
helm.sh/chart: {{ include "trmnl-agent.chart" . }}
{{ include "trmnl-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "trmnl-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "trmnl-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "trmnl-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "trmnl-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create secret name
*/}}
{{- define "trmnl-agent.secretName" -}}
{{- printf "%s-secret" (include "trmnl-agent.fullname" .) }}
{{- end }}

{{/*
Create configmap name
*/}}
{{- define "trmnl-agent.configMapName" -}}
{{- printf "%s-config" (include "trmnl-agent.fullname" .) }}
{{- end }}