'use client';

type LinkInfo = {
  url: string;
  url_type: string;
  description: string;
};

type Props = {
  links: LinkInfo[];
};


const OtherLinks = ({links}: Props) => {

  return (
    <div className="flex flex-col rounded-sm border border-gray-200">
      <h4 className="text-left text-xl font-bold bg-cyan-700 text-white pl-3 p-2 rounded-t-sm">
        Other Relevant Links
      </h4>
      {links.length > 0 &&
        <ul className="list-disc pl-6 space-y-2 text-gray-700 p-2">
          {links.map((link) => (
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
      {links.length == 0 && (
        <p className='text-gray-600 text-center py-2'>No other links provided.</p>
      )}
    </div>
  );
};

export default OtherLinks;
