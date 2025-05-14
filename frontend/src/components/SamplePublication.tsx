import React from 'react';

type LinkInfo = {
  url: string;
  url_type: string;
  description: string;
};

type Props = {
  links: LinkInfo[];
};

const SamplePublication = async ({ links }: Props) => {
  const doiLinks = links.filter((link) => link.url_type === 'DOI');
  const otherLinks = links.filter((link) => link.url_type !== 'DOI');

  const publications = await Promise.all(
    doiLinks.map(async (link) => {
      const doi = link.url.replace(/^https?:\/\/(dx\.)?doi\.org\//, ''); // clean DOI
      try {
        const res = await fetch(
          `https://citation.doi.org/format?doi=${doi}&style=apa&lang=en-US`,
          {
            headers: {
              Accept: 'text/x-bibliography',
            },
            cache: 'no-store',
          }
        );
        const data = await res.text();
        return data;
      } catch (error) {
        console.error('Failed to fetch citation for', link.url, error);
        return link.url; // fallback
      }
    })
  );

  return (
    <div>
      {publications.length > 0 && (
        <div className="flex flex-col rounded-sm">
          <h4 className="text-left text-xl font-bold bg-cyan-700 text-white pl-3 p-2 rounded-t-sm">
            Sample Publication
          </h4>
          <ul className="list-disc pl-5 space-y-2 text-gray-700">
            {publications.map((citation, idx) => (
              <li key={idx}>{citation}</li>
            ))}
          </ul>
        </div>
      )}
      {otherLinks.length > 0 && (
        <div className="flex flex-col rounded-sm mt-4">
          <h4 className="text-left text-xl font-bold bg-cyan-700 text-white pl-3 p-2 rounded-t-sm">
            Other Relevant Links
          </h4>
          <ul className="list-disc pl-5 space-y-2 text-gray-700">
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
        </div>
      )}
    </div>
  );
};

export default SamplePublication;
