'use client';

import { useState } from 'react';
import SampleMap from './SampleMap';

import type { Props as SampleMapProps } from './SampleMap';

const LandingPageMapWrapper = (props: SampleMapProps) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="border border-gray-200 rounded-sm">
      <button
        className="text-left text-xl font-bold bg-cyan-700 text-white pl-3 cursor-pointer p-2 rounded-t-sm w-full"
        onClick={() => setIsOpen(!isOpen)}
      >
        Sample Map {isOpen ? '▲' : '▼'}
      </button>

      <div
        className={`transition-all duration-300 ease-in-out overflow-hidden ${
          isOpen ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="p-4 rounded-b-sm">
          <SampleMap {...props} />
        </div>
      </div>
    </div>
  );
};

export default LandingPageMapWrapper;
