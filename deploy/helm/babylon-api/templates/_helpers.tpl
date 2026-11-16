{{/*
SPDX-FileCopyrightText: Copyright (C) 2022-2026 Cosmo Tech
SPDX-License-Identifier: MIT
*/}}
{{- define "babylon-api.labels" -}}
app.kubernetes.io/name: babylon-api
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{- define "babylon-api.selectorLabels" -}}
app.kubernetes.io/name: babylon-api
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "babylon-api.image" -}}
{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}
{{- end }}
