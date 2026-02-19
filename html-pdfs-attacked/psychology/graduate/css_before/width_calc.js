var w={};
w['c012c709a39c1']='Freud\'s notion of';
w['c6178cd6c0a3b']='frequently point out that the former';
w['cc3d9a4141c3a']='failure identity';
w['cd1380e4906fd']='disproving the statement: \"Most people only use 10 percent of their brains\"';
w['c206db5947f8d']='based on a client\'s current income';
w['cd5d9dec52686']='5.8 lbs';
w['c123694f448a5']='historical human events';
w['cc69a3657ff25']='theoretical';
w['cfb639adad80f']='neutral';
w['cbb4b6da2d9ea']='7, 3, 8';
w['c2cd9633ee2d1']='inherent positivity and goal-directed';
w['cd637c08975dc']='Performance subtests';
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