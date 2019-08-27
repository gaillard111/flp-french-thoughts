<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\DynamicPage;

class DynamicPagesController extends Controller
{
    /**
     * @Route("/page/{slug}", name="dynamic_page")
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function indexAction($slug)
    {
        /** @var DynamicPage $page */
        $page = $this->getDoctrine()->getRepository(DynamicPage::class)->findOneBy(['slug' => $slug]);

        if (!$page) {
            throw new NotFoundHttpException("Page not found");
        }

        return $this->render('@Thought/dynamicPage.html.twig', [
            'title' => $page->getTitle(),
            'text'  => $page->getText()
        ]);
    }
}
