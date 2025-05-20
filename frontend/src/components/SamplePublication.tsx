'use client';

import React, { useEffect, useState, useMemo } from 'react';

type LinkInfo = {
  url: string;
  url_type: string;
  description: string;
};

type Props = {
  links: LinkInfo[];
};

const STYLES = ['apa', 'chicago-author-date'];

const SamplePublication: React.FC<Props> = ({ links }) => {
  const [citations, setCitations] = useState<string[]>([]);
  const [style, setStyle] = useState('apa');

  const doiLinks = useMemo(() => links.filter(link => link.url_type === 'DOI'), [links]);
  const otherLinks = useMemo(() => links.filter(link => link.url_type !== 'DOI'), [links]);

  useEffect(() => {
    const fetchCitations = async () => {
      const results: string[] = [];

      for (const link of doiLinks) {
        const doi = link.url.replace(/^https?:\/\/(dx\.)?doi\.org\//, '');
        try {
          const res = await fetch(
            `https://citation.doi.org/format?doi=${encodeURIComponent(doi)}&style=${style}&lang=en-US`,
            {
              headers: { Accept: 'text/x-bibliography' },
            }
          );
          const data = await res.text();
          results.push(data);
        } catch {
          results.push(`Error fetching citation for ${doi}`);
        }
      }

      setCitations(results);
    };

    if (doiLinks.length > 0) {
      fetchCitations();
    }
  }, [doiLinks, style]);

  return (
    <div>
      <div className="flex flex-col rounded-sm mb-6 border border-gray-200">
        <h4 className="text-left text-xl font-bold bg-cyan-700 text-white pl-3 p-2 rounded-t-sm">
          Publications & Datasets
        </h4>
        {citations.length > 0 && (
          <ol className="list-decimal pl-6 space-y-2 text-gray-700 p-2">
            {citations.map((citation, index) => (
              <li key={index}>{citation}</li>
            ))}
          </ol>
        )}
        
        {citations.length > 0 && (
          <div className="pl-6 p-2">
            <label htmlFor="style-select" className="font-semibold">Citation Style:</label>
            <select
              id="style-select"
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="ml-2 p-1 border rounded"
            >
              {STYLES.map((s) => (
                <option key={s} value={s}>{s.toUpperCase()}</option>
              ))}
            </select>
          </div>
        )}
        
        {citations.length == 0 && (
          <p className='text-gray-600 text-center py-2'>No citations provided.</p>
        )}
      </div>

      <div className="flex flex-col rounded-sm border border-gray-200">
        <h4 className="text-left text-xl font-bold bg-cyan-700 text-white pl-3 p-2 rounded-t-sm">
          Other Relevant Links
        </h4>
        {otherLinks.length > 0 &&
          <ul className="list-disc pl-6 space-y-2 text-gray-700 p-2">
            {otherLinks.map((link) => (
              <li key={link.url}>
                <a
                  href={link.url}
                  className="text-blue-600 hover:underline break-all"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {link.url}
                </a>
                {link.description && (
                  <span className="ml-1 text-gray-500">– {link.description}</span>
                )}
              </li>
            ))}
          </ul>
        }
        {otherLinks.length == 0 && (
          <p className='text-gray-600 text-center py-2'>No other links provided.</p>
        )}
      </div>
    </div>
  );
};

export default SamplePublication;
