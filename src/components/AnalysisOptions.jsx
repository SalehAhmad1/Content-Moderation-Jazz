import { Switch } from '@headlessui/react';
import { cn } from '../utils/cn';

export default function AnalysisOptions({ options, setOptions }) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-lg font-semibold mb-4">Analysis Options</h2>
      <div className="space-y-4">
        <SwitchOption
          enabled={options.detectAbusive}
          onChange={(value) => setOptions((prev) => ({ ...prev, detectAbusive: value }))}
          label="Detect Abusive Content"
          description="Identify hate speech, harassment, and offensive language"
        />
        <SwitchOption
          enabled={options.detectViolent}
          onChange={(value) => setOptions((prev) => ({ ...prev, detectViolent: value }))}
          label="Detect Violent Content"
          description="Identify violence, threats, and dangerous behavior"
        />
        <SwitchOption
          enabled={options.detectNSFW}
          onChange={(value) => setOptions((prev) => ({ ...prev, detectNSFW: value }))}
          label="Detect NSFW Content"
          description="Identify adult content and inappropriate material"
        />
        <SwitchOption
          enabled={options.detectPolitical}
          onChange={(value) => setOptions((prev) => ({ ...prev, detectPolitical: value }))}
          label="Detect Political Content"
          description="Identify political bias and politically charged language"
        />
        <SwitchOption
          enabled={options.detectReligious}
          onChange={(value) => setOptions((prev) => ({ ...prev, detectReligious: value }))}
          label="Detect Religious Content"
          description="Identify religious content and potentially sensitive material"
        />
      </div>
    </div>
  );
}

function SwitchOption({ enabled, onChange, label, description }) {
  return (
    <Switch.Group>
      <div className="flex items-start">
        <Switch
          checked={enabled}
          onChange={onChange}
          className={cn(
            enabled ? 'bg-blue-600' : 'bg-gray-200',
            'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out'
          )}
        >
          <span
            className={cn(
              enabled ? 'translate-x-6' : 'translate-x-1',
              'inline-block h-4 w-4 transform rounded-full bg-white transition duration-200 ease-in-out mt-1'
            )}
          />
        </Switch>
        <div className="ml-4">
          <Switch.Label className="font-medium text-gray-900">{label}</Switch.Label>
          <Switch.Description className="text-sm text-gray-500">{description}</Switch.Description>
        </div>
      </div>
    </Switch.Group>
  );
}