{{/*
Expand the name of the chart.
*/}}
{{- define "monitor-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "monitor-agent.fullname" -}}
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
{{- define "monitor-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "monitor-agent.labels" -}}
helm.sh/chart: {{ include "monitor-agent.chart" . }}
{{ include "monitor-agent.selectorLabels" . }}
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
{{- define "monitor-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "monitor-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use.
*/}}
{{- define "monitor-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "monitor-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the config map name.
*/}}
{{- define "monitor-agent.configMapName" -}}
{{- printf "%s-config" (include "monitor-agent.fullname" .) }}
{{- end }}

{{/*
Create the kubeconfig mount path.
*/}}
{{- define "monitor-agent.kubeConfigMountPath" -}}
{{- printf "/var/run/%s/kubeconfig" (include "monitor-agent.name" .) }}
{{- end }}