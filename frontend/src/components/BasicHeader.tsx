import React from 'react'
import Image from 'next/image';

const BasicHeader = () => {
  return (
    <div className='bg-sesar-main'>
        <Image 
        src="/sesar_logo.png" 
        alt="SESAR LOGO" 
        width={150} 
        height={200} 
        />
    </div>
  )
}

export default BasicHeader