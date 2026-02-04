'use client';

import { DepartmentProfile } from '@/types';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Edit2 } from 'lucide-react';

interface DepartmentProfileCardProps {
  profile: DepartmentProfile;
  onEdit: (profile: DepartmentProfile) => void;
}

export function DepartmentProfileCard({
  profile,
  onEdit,
}: DepartmentProfileCardProps) {
  const weights = [
    { label: 'Bias & Fairness', value: profile.weights.bias },
    { label: 'Data Grounding', value: profile.weights.dataGrounding },
    { label: 'Explainability', value: profile.weights.explainability },
    { label: 'Ethical Alignment', value: profile.weights.ethicalAlignment },
    { label: 'Human Control', value: profile.weights.humanControl },
    { label: 'Legal Compliance', value: profile.weights.legal },
    { label: 'Security', value: profile.weights.security },
    { label: 'Quality', value: profile.weights.quality },
  ];

  return (
    <Card className="border-slate-200 p-6">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900">
          {profile.name}
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onEdit(profile)}
          className="gap-2"
        >
          <Edit2 className="h-4 w-4" />
          Edit
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {weights.map((item) => (
          <div key={item.label} className="flex items-center justify-between p-2 bg-slate-50 rounded">
            <span className="text-xs text-slate-600 font-medium">
              {item.label.split('&')[0]}
            </span>
            <span className="text-sm font-semibold text-slate-900">
              {item.value}%
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-200">
        <p className="text-xs text-slate-500">
          Total Weight:{' '}
          <span className="font-semibold text-slate-900">
            {weights.reduce((sum, w) => sum + w.value, 0)}%
          </span>
        </p>
      </div>
    </Card>
  );
}
