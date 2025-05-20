'use client';

import { useState } from 'react';
import SampleFamily from './SampleFamily';

import type { Props as SampleFamilyProps } from './SampleFamily';

const LandingPageFamilyWrapper = (props: SampleFamilyProps) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="border border-gray-200 rounded-sm">
      <button
        className="text-left text-xl font-bold bg-cyan-700 text-white pl-3 cursor-pointer p-2 rounded-t-sm w-full"
        onClick={() => setIsOpen(!isOpen)}
      >
        Sample Family {isOpen ? '▲' : '▼'}
      </button>

      {isOpen && (
        <div className="p-4 rounded-b-sm">
          <SampleFamily {...props} />
        </div>
      )}
    </div>
  );
};

export default LandingPageFamilyWrapper;
