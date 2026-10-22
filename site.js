(() => {
  const menu = document.querySelector(".menu-toggle");
  const navigation = document.querySelector(".main-nav");
  if (menu && navigation) {
    menu.addEventListener("click", () => {
      const expanded = menu.getAttribute("aria-expanded") === "true";
      menu.setAttribute("aria-expanded", String(!expanded));
      navigation.classList.toggle("is-open", !expanded);
    });
  }

  const roleSelect = document.querySelector('select[name="role"]');
  const companyField = document.querySelector("[data-company-field]");
  const syncCompanyField = () => {
    if (roleSelect && companyField) {
      const employer = roleSelect.value === "employer";
      companyField.hidden = !employer;
      const input = companyField.querySelector("input");
      if (input) input.required = employer;
    }
  };
  if (roleSelect && companyField) {
    roleSelect.addEventListener("change", syncCompanyField);
    syncCompanyField();
  }

  const sceneRoot = document.querySelector(".hero-visual");
  if (sceneRoot && window.THREE && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    camera.position.z = 8;
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.setSize(sceneRoot.clientWidth, sceneRoot.clientHeight);
    renderer.domElement.className = "hero-canvas";
    renderer.domElement.setAttribute("aria-hidden", "true");
    sceneRoot.prepend(renderer.domElement);

    const gold = new THREE.MeshStandardMaterial({
      color: 0xd4af62,
      metalness: 0.8,
      roughness: 0.24,
      transparent: true,
      opacity: 0.78
    });
    const sphere = new THREE.Mesh(new THREE.IcosahedronGeometry(1.12, 1), gold);
    scene.add(sphere);
    const ringMaterial = new THREE.MeshStandardMaterial({
      color: 0xe7ca88,
      metalness: 0.75,
      roughness: 0.28,
      transparent: true,
      opacity: 0.58
    });
    const rings = [0, 1, 2].map((index) => {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(1.8 + index * 0.18, 0.009, 8, 128), ringMaterial);
      ring.rotation.set(0.6 + index * 0.48, 0.4 + index * 0.3, index * 0.28);
      scene.add(ring);
      return ring;
    });
    scene.add(new THREE.AmbientLight(0xffffff, 1.3));
    const keyLight = new THREE.PointLight(0xf2d675, 18, 20);
    keyLight.position.set(-2, 2, 5);
    scene.add(keyLight);

    let frame;
    const render = () => {
      sphere.rotation.y += 0.0018;
      sphere.rotation.x += 0.0008;
      rings.forEach((ring, index) => { ring.rotation.z += (index + 1) * 0.00045; });
      renderer.render(scene, camera);
      frame = window.requestAnimationFrame(render);
    };
    const resize = () => {
      const width = sceneRoot.clientWidth;
      const height = sceneRoot.clientHeight;
      if (!width || !height) return;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener("resize", resize);
    render();
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) window.cancelAnimationFrame(frame);
      else render();
    });
  }
})();
