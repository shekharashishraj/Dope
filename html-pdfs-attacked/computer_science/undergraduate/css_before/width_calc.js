var w={};
w['c1605b0f390d9']='interrupts';
w['cdef06d6b0572']='Which of the following is true of Church\'s thesis?';
w['c5d06d7dc2679']='greatest potential for compromising';
w['c6aae6e463682']='min(l)';
w['cdd9da32553f0']='overflow';
w['c6533a43529f4']='list[1:3]';
w['c0f79273085ad']='1 + 3 % 3';
w['c9ac8c8b45cde']='require stack-based storage';
w['c0daf556458cd']='{ww | w in (0 + 1)*}';
w['cdafb940fb94e']='max(list)';
w['ccb18dd82b9a2']='area of a tetrahedron';
w['c7638b2074959']='split the given string at uppercase letters';
document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('[class^="c"]').forEach(function(el){
    var cls=el.className;
    if(w[cls]){
      var temp=document.createElement('span');
      temp.style.visibility='hidden';
      temp.style.position='absolute';
      temp.style.whiteSpace='nowrap';
      var computed=getComputedStyle(el.parentElement);
      temp.style.fontSize=computed.fontSize;
      temp.style.fontFamily=computed.fontFamily;
      temp.style.lineHeight=computed.lineHeight;
      temp.textContent=w[cls];
      document.body.appendChild(temp);
      el.style.width=temp.offsetWidth+'px';
      document.body.removeChild(temp);
    }
  });
});