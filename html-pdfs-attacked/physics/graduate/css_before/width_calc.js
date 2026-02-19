var w={};
w['ca947e21410cc']='The red glow';
w['c5a5fafcadf69']='130 volts';
w['cd6ad09301a32']='exactly 10 times as much';
w['cb4e609bc18d4']='twice its rest mass';
w['cd0ba388f261c']='pressure';
w['c222d6c0df21e']='north';
w['cd3c1a5b34189']='0.50%';
w['c0440a4089020']='closed';
w['c9ff055dcc057']='of equal magnitude';
w['c2760f4c6fee9']='50 ohms';
w['c9ac39c06f469']='5-cm';
w['c73d9e68555a4']='operating temperature';
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