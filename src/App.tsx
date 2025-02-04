import { createRoot } from 'react-dom/client'

import { LiveReload } from './LiveReload'
import VideoPlayer from './VideoPlayer'

import React, { useState, useEffect } from 'react';

const SampleView = (props) => {
   // TODO prefix
  if(props.src.includes("youtube")) {
    return (
      <div>
        <iframe src="https://www.youtube.com/embed/UrRZ-kKnBEw?si=test&amp;loop=1&amp;start=150&amp;end=151&amp;showinfo=0&amp;playlist=UrRZ-kKnBEw;start=150&amp;end=151"
          title="YouTube" 
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
      </div>
    )
  }
  return (
      <VideoPlayer src={props.src}/>
  )
};

const App = () => {
  const [samples, setSamples] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/samples')
      .then(response => response.json())
      .then(xs => setSamples(xs))
  }, []);

  return (
    <div className="flex flex-col min-h-screen max-h-screen">
      <div className="flex items-center justify-between px-8 py-8  h-14 shadow-sm text-gray-500 text-xl bg-gray-200">
        <div class="text-left">
          Home
        </div>

                
        <form class="max-w-lg mx-auto">
            <div class="flex">
                <div class="relative w-full">
                    <input type="search" id="search-dropdown" class="block border-solid
                    p-2.5 w-full z-20 text-sm text-gray-900 bg-gray-50
                    rounded-e-sm border
                    border-gray-300 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Filter..." required />
                    <button type="submit" class="absolute top-0 end-0 p-2.5
                    text-sm font-medium h-full text-white bg-blue-700
                    rounded-e-sm border border-blue-700 hover:bg-blue-800
                    focus:ring-4 focus:outline-none focus:ring-blue-300">
                        <svg class="w-4 h-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
                            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"/>
                        </svg>
                        <span class="sr-only">Search</span>
                    </button>
                </div>
            </div>
        </form>


        <div class='max-w-md flex-1 mx-5'>
            <div class="relative flex items-center w-full h-10 rounded-sm focus-within:shadow-sm bg-white overflow-hidden">
                <div class="grid place-items-center h-full w-10 text-gray-300">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>

                <input 
                  class="peer h-full w-full outline-none text-sm text-gray-700 pr-2"
                  type="text"
                  id="search"
                  placeholder="Search.." /> 
            </div>
        </div>
      </div>
      <div className="bg-gray-100 py-8 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-4 gap-4">
          {
            samples.map((x) => (
              <div>
                <SampleView src={x.path}/>
                <div>{x.annotation}</div>
              </div>
            ))
          }
        </div>
      </div>
    </div>
  )
}

document.addEventListener('DOMContentLoaded', () => {
  const root = createRoot(document.getElementById('root')!)
  root.render(
    <>
      <LiveReload />
      <App />
    </>,
  )
})
