'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/hooks/use-toast';
import { Save } from 'lucide-react';

interface SettingsFormProps {
  onSave?: () => void;
}

export function SettingsForm({ onSave }: SettingsFormProps) {
  const { toast } = useToast();
  const [minScore, setMinScore] = useState(70);
  const [redThreshold, setRedThreshold] = useState(70);
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [slackAlerts, setSlackAlerts] = useState(false);

  const handleSave = () => {
    toast({
      title: 'Settings Saved',
      description: 'Your alert thresholds have been updated successfully.',
    });
    onSave?.();
  };

  return (
    <div className="space-y-6">
      {/* Dimension Weighting */}
      <Card className="border-border p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Dimension Weighting
        </h3>
        <div className="space-y-4">
          {[
            'Bias & Fairness',
            'Data Grounding & Drift',
            'Explainability & Transparency',
            'Ethical Alignment',
            'Human Control',
            'Legal Compliance',
            'Security & Robustness',
            'Response Quality',
          ].map((dimension, i) => (
            <div key={dimension}>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-muted-foreground">
                  {dimension}
                </label>
                <span className="text-sm font-semibold text-foreground">
                  {Math.round(12.5)}%
                </span>
              </div>
              <Slider
                min={0}
                max={100}
                step={5}
                value={[12.5]}
                className="w-full"
              />
            </div>
          ))}
        </div>
        <div className="mt-6 pt-4 border-t border-slate-200">
          <p className="text-sm font-medium text-slate-900">
            Total Weight:{' '}
            <span className="text-blue-600">100%</span>
          </p>
        </div>
      </Card>

      {/* Alert Thresholds */}
      <Card className="border-border p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Alert Thresholds
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Minimum Acceptable Ethical Score
            </label>
            <Input
              type="number"
              min="0"
              max="100"
              value={minScore}
              onChange={(e) => setMinScore(parseInt(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Conversations below this score will be flagged for review
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Red Alert Threshold
            </label>
            <Input
              type="number"
              min="0"
              max="100"
              value={redThreshold}
              onChange={(e) => setRedThreshold(parseInt(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Conversations below this score will be marked as violations
            </p>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={emailAlerts}
                onChange={(e) => setEmailAlerts(e.target.checked)}
                className="rounded border-border bg-background"
              />
              <span className="text-sm font-medium text-muted-foreground">
                Enable Email Alerts
              </span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={slackAlerts}
                onChange={(e) => setSlackAlerts(e.target.checked)}
                className="rounded border-border bg-background"
              />
              <span className="text-sm font-medium text-muted-foreground">
                Enable Slack Alerts
              </span>
            </label>
          </div>
        </div>
      </Card>

      {/* Save Button */}
      <Button
        onClick={handleSave}
        className="w-full bg-primary hover:bg-primary/90 text-primary-foreground gap-2"
        size="lg"
      >
        <Save className="h-4 w-4" />
        Save Settings
      </Button>
    </div>
  );
}
