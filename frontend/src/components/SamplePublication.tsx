'use client';

import React, { useEffect, useState} from 'react';

type LinkInfo = {
  url: string;
  url_type: string;
  description: string;
};

type Props = {
  links: LinkInfo[];
};

const STYLES = ['apa', 'chicago-author-date'];

const SamplePublication = ({ links } : Props) => {
  const [citations, setCitations] = useState<string[]>([]);
  const [style, setStyle] = useState('apa');

  useEffect(() => {
    const fetchCitations = async () => {
      const results: string[] = [];

      for (const link of links) {
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

    if (links.length > 0) {
      fetchCitations();
    }
  }, [links, style]);

  return (
    <div className="flex flex-col rounded-sm border border-gray-200">
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
  );
};

export default SamplePublication;
