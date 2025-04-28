import React from 'react';
import BasicHeader from "@/components/BasicHeader";


const Layout = ({children}:{children: React.ReactNode}) => {
  return (
    <div>
        <BasicHeader />
        {children}
    </div>
  )
}

export default Layout
