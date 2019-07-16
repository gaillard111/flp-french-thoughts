<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\File\UploadedFile;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Form\CKEditorImageForm;

class UtilController extends Controller
{
    /**
     * @Route("/util/image_upload", name="ckeditor_image_upload")
     *
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function indexAction(Request $request)
    {

        $form = $this->createForm(CKEditorImageForm::class);
        $form->handleRequest($request);

        if ($form->isSubmitted()) {
            /** @var UploadedFile $uploadedFile */
            $uploadedFile = $form->get('image')->getData();
            $dir = $this->getParameter('kernel.root_dir') . '/../web/images/ckeditor/';
            $name = uniqid('ckeditor');
            $uploadedFile->move($dir, $name);

            return $this->render('@Thought/Util/img_upload.html.twig', [
                'image_url' => '/images/ckeditor/' . $name
            ]);
        }


        return $this->render('@Thought/Util/img_upload.html.twig', [
            'form' => $form->createView(),
        ]);
    }
}
