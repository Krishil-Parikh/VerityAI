'use client';

import { useState } from 'react';
import { DepartmentProfile } from '@/types';
import { SettingsForm } from '@/components/admin/SettingsForm';
import { DepartmentProfileCard } from '@/components/admin/DepartmentProfileCard';
import { Card } from '@/components/ui/card';
import { dummyDepartments } from '@/lib/dummyData';

export default function SettingsPage() {
  const [departments, setDepartments] = useState<DepartmentProfile[]>(
    dummyDepartments
  );

  const handleEditDepartment = (profile: DepartmentProfile) => {
    // In a real app, this would open a modal to edit the department
    console.log('Edit department:', profile);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">
          Configuration & Settings
        </h1>
        <p className="text-slate-600 mt-1">
          Manage ethical scoring weights, alert thresholds, and department profiles
        </p>
      </div>

      <SettingsForm />

      {/* Department Profiles */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 mb-4">
          Department Profiles
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {departments.map((dept) => (
            <DepartmentProfileCard
              key={dept.id}
              profile={dept}
              onEdit={handleEditDepartment}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
