import { useState } from 'react'
import { Save, Bell, Shield, Activity } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({
    // Alert Thresholds
    costAnomalyThreshold: 400000,
    latencySpikeThreshold: 5000,
    errorRateThreshold: 5,
    qualityDegradationThreshold: 0.7,
    
    // Notifications
    emailNotifications: true,
    slackNotifications: false,
    datadogAlerts: true,
    
    // Security
    autoRemediation: true,
    threatBlocking: false,
    piiRedaction: true,
    
    // Performance
    batchSize: 10,
    flushInterval: 1,
    retentionDays: 30,
  })

  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    // Save settings to backend
    console.log('Saving settings:', settings)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Configure GuardianAI monitoring preferences
        </p>
      </div>

      {/* Alert Thresholds */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Bell className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Alert Thresholds</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Cost Anomaly Threshold (tokens/hour)
            </label>
            <input
              type="number"
              value={settings.costAnomalyThreshold}
              onChange={(e) => handleChange('costAnomalyThreshold', Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Latency Spike Threshold (ms)
            </label>
            <input
              type="number"
              value={settings.latencySpikeThreshold}
              onChange={(e) => handleChange('latencySpikeThreshold', Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Error Rate Threshold (%)
            </label>
            <input
              type="number"
              value={settings.errorRateThreshold}
              onChange={(e) => handleChange('errorRateThreshold', Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Quality Degradation Threshold
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="1"
              value={settings.qualityDegradationThreshold}
              onChange={(e) => handleChange('qualityDegradationThreshold', Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Bell className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Notification Channels</h2>
        </div>
        
        <div className="space-y-4">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.emailNotifications}
              onChange={(e) => handleChange('emailNotifications', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Email Notifications</span>
          </label>
          
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.slackNotifications}
              onChange={(e) => handleChange('slackNotifications', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Slack Notifications</span>
          </label>
          
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.datadogAlerts}
              onChange={(e) => handleChange('datadogAlerts', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Datadog Alerts</span>
          </label>
        </div>
      </div>

      {/* Security */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Security Settings</h2>
        </div>
        
        <div className="space-y-4">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.autoRemediation}
              onChange={(e) => handleChange('autoRemediation', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Automatic Incident Remediation</span>
          </label>
          
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.threatBlocking}
              onChange={(e) => handleChange('threatBlocking', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Block Detected Threats</span>
          </label>
          
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.piiRedaction}
              onChange={(e) => handleChange('piiRedaction', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Automatic PII Redaction</span>
          </label>
        </div>
      </div>

      {/* Performance */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Activity className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Performance Settings</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Batch Size
            </label>
            <input
              type="number"
              value={settings.batchSize}
              onChange={(e) => handleChange('batchSize', Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Flush Interval (seconds)
            </label>
            <input
              type="number"
              value={settings.flushInterval}
              onChange={(e) => handleChange('flushInterval', Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Retention Days
            </label>
            <input
              type="number"
              value={settings.retentionDays}
              onChange={(e) => handleChange('retentionDays', Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end gap-3">
        {saved && (
          <span className="text-sm text-success-600 dark:text-success-400 flex items-center gap-2">
            Settings saved successfully!
          </span>
        )}
        <button
          onClick={handleSave}
          className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
        >
          <Save className="h-4 w-4" />
          Save Changes
        </button>
      </div>
    </div>
  )
}
