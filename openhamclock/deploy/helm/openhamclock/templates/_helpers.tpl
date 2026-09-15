{{/*
Expand the name of the chart.
*/}}
{{- define "openhamclock.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Create a fully qualified app name.

For the default release this becomes:

openhamclock-openhamclock

*/}}
{{- define "openhamclock.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "openhamclock.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}


{{/*
Common labels.
*/}}
{{- define "openhamclock.labels" -}}
app.kubernetes.io/name: {{ include "openhamclock.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end }}


{{/*
Selector labels.
*/}}
{{- define "openhamclock.selectorLabels" -}}
app.kubernetes.io/name: {{ include "openhamclock.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}