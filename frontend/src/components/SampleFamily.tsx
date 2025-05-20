'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

export type Props = {
  parent_igsn: string;
  sibling_igsns: string[];
  children_igsns: string[];
};

const CollapsibleSection = ({
  title,
  isOpen,
  toggle,
  children,
}: {
  title: string;
  isOpen: boolean;
  toggle: () => void;
  children: React.ReactNode;
}) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [maxHeight, setMaxHeight] = useState('0px');

  useEffect(() => {
    if (isOpen && contentRef.current) {
      setMaxHeight(`${contentRef.current.scrollHeight}px`);
    } else {
      setMaxHeight('0px');
    }
  }, [isOpen]);

  return (
    <div>
      <button onClick={toggle} className="font-semibold hover:underline">
        {title} {isOpen ? '▲' : '▼'}
      </button>
      <div
        ref={contentRef}
        className="transition-all duration-300 ease-in-out overflow-hidden"
        style={{ maxHeight }}
      >
        <div className="pl-4 pt-1">{children}</div>
      </div>
    </div>
  );
};

const SampleFamily = ({ parent_igsn, sibling_igsns, children_igsns }: Props) => {
  const [showParent, setShowParent] = useState(true);
  const [showSiblings, setShowSiblings] = useState(true);
  const [showChildren, setShowChildren] = useState(true);

  const hasData = parent_igsn != null || sibling_igsns.length > 0 || children_igsns.length > 0;

  if (!hasData) {
    return <p className="text-gray-600 text-center py-2">No sample family found.</p>;
  }

  return (
    <div className="space-y-4">
      {parent_igsn && (
        <CollapsibleSection
          title="Parent"
          isOpen={showParent}
          toggle={() => setShowParent(!showParent)}
        >
          <p>
            <Link href={`/sample/igsn/${parent_igsn}`} className="text-gray-600 hover:underline">
              {parent_igsn}
            </Link>
          </p>
        </CollapsibleSection>
      )}

      {sibling_igsns.length > 0 && (
        <CollapsibleSection
          title="Siblings"
          isOpen={showSiblings}
          toggle={() => setShowSiblings(!showSiblings)}
        >
          {sibling_igsns.map((sibling) => (
            <p key={sibling}>
              <Link href={`/sample/igsn/${sibling}`} className="text-gray-600 hover:underline">
                {sibling}
              </Link>
            </p>
          ))}
        </CollapsibleSection>
      )}

      {children_igsns.length > 0 && (
        <CollapsibleSection
          title="Children"
          isOpen={showChildren}
          toggle={() => setShowChildren(!showChildren)}
        >
          {children_igsns.map((child) => (
            <p key={child}>
              <Link href={`/sample/igsn/${child}`} className="text-gray-600 hover:underline">
                {child}
              </Link>
            </p>
          ))}
        </CollapsibleSection>
      )}
    </div>
  );
};

export default SampleFamily;
