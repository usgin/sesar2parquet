type FileInfo = {
  file_name: string;
  file_type: string;
  path_to_file: string;
};

type Props = {
  files: FileInfo[];
};

const ImageGallery = ({ files }: Props) => {
  const baseUrl = process.env.NEXT_PUBLIC_API2_BASE_URL;

  const renderImageGrid = () => {
    const count = files.length;

    if (count <= 3) {
      // 1–3 images: one row, naturally responsive
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 p-4">
          {files.map((file) => (
            <ImageCard key={file.file_name} file={file} baseUrl={baseUrl} />
          ))}
        </div>
      );
    }

    if (count === 4) {
      // 4 images: two rows of 2
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 gap-4 p-4">
          {files.map((file) => (
            <ImageCard key={file.file_name} file={file} baseUrl={baseUrl} />
          ))}
        </div>
      );
    }

    if (count === 5) {
      // 5 images: first 3 in one row, last 2 in another
      return (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 p-4">
            {files.slice(0, 3).map((file) => (
              <ImageCard key={file.file_name} file={file} baseUrl={baseUrl} />
            ))}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 gap-4 px-4 pb-4">
            {files.slice(3).map((file) => (
              <ImageCard key={file.file_name} file={file} baseUrl={baseUrl} />
            ))}
          </div>
        </>
      );
    }

    return null;
  };

  return (
    <div className="flex flex-col rounded-sm border border-gray-200">
      <h4 className="text-left text-xl font-bold bg-cyan-700 text-white pl-3 p-2 rounded-t-sm">
        Image Gallery
      </h4>

      {files.length === 0 ? (
        <p className="text-center text-gray-500 py-6">No images to display.</p>
      ) : (
        renderImageGrid()
      )}
    </div>
  );
};

const ImageCard = ({
  file,
  baseUrl,
}: {
  file: FileInfo;
  baseUrl: string | undefined;
}) => (
  <a
    href={`${baseUrl}/uploads/${file.path_to_file}`}
    target="_blank"
    rel="noopener noreferrer"
    className="block border rounded-md overflow-hidden shadow-sm hover:shadow-md transition"
  >
    <img
      src={`${baseUrl}/uploads/${file.path_to_file}`}
      alt={file.file_name}
      className="w-full h-50 object-cover"
    />
  </a>
);

export default ImageGallery;
