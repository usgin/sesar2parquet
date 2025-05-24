'use client';

type FileInfo = {
  file_name: string;
  file_type: string;
  path_to_file: string;
};

type Props = {
  files: FileInfo[];
};


const OtherFiles = ({files}: Props) => {
  const baseUrl = process.env.NEXT_PUBLIC_API2_BASE_URL;

  return (
    <div className="flex flex-col rounded-sm border border-gray-200">
      <h4 className="text-left text-xl font-bold bg-cyan-700 text-white pl-3 p-2 rounded-t-sm">
        Other Relevant Files
      </h4>
      <ul className="list-disc pl-6 space-y-2 text-gray-700 p-2">
        {files.map((file) => (
          <li key={file.file_name}>
            <a
              href={`${baseUrl}/uploads/${file.path_to_file}`}
              className="text-blue-600 hover:underline break-all"
              target="_blank"
              rel="noopener noreferrer"
            >
              {file.file_name}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default OtherFiles;
