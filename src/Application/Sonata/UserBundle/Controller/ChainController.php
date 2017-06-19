<?php

namespace Application\Sonata\UserBundle\Controller;

use Application\Sonata\UserBundle\Form\Type\ChainType;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Chain;

class ChainController extends Controller
{
    /**
     * @Route("/chains", name="sonata_user_chains")
     * @param Request $request
     * @return Response
     */
    public function listAction(Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $chains = $em->getRepository('ThoughtBundle:Chain')->findBy(array(
            'user' => $this->getUser(),
        ));

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            100
        );

        return $this->render('ApplicationSonataUserBundle:Chain:list.html.twig', array(
            'chains' => $pagination,
        ));
    }

    /**
     * @Route("/chain/create", name="sonata_user_chain_create")
     *
     * @param Request $request
     * @return Response
     */
    public function createAction(Request $request)
    {
        $chain = new Chain();
        $em = $this->getDoctrine()->getManager();

        $form = $this->createForm(new ChainType(), $chain);
        $form->handleRequest($request);

        if ($request->getMethod() == 'POST') {
            if ($form->isValid()) {
                $chain->setUser($this->getUser());
                $em->persist($chain);
                $em->flush();

                return $this->redirect($this->generateUrl('sonata_user_chains'));
            }
        }

        return $this->render('ApplicationSonataUserBundle:Chain:create.html.twig', array(
            'form' => $form->createView(),
        ));
    }

    /**
     * @Route("/chain/{chainId}/edit", name="sonata_user_chain_edit", requirements={"chainId"="\d+"})
     *
     * @param Request $request
     * @param int     $chainId
     * @return \Symfony\Component\HttpFoundation\RedirectResponse|Response
     */
    public function editAction(Request $request, $chainId)
    {
        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.not_exist'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        if (!$this->checkOwner($chain)) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.access_denied'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        $form = $this->createForm(new ChainType(), $chain);
        $form->handleRequest($request);

        if ($request->getMethod() == 'POST') {
            if ($form->isValid()) {
                $chain->setUser($this->getUser());
                $em->persist($chain);
                $em->flush();

                return $this->redirect($this->generateUrl('sonata_user_chains'));
            }
        }

        return $this->render('ApplicationSonataUserBundle:Chain:edit.html.twig', array(
            'form' => $form->createView(),
        ));
    }

    /**
     * @Route("/chain/{chainId}/remove", name="sonata_user_chain_remove", requirements={"chainId"="\d+"})
     *
     * @param int $chainId
     * @return \Symfony\Component\HttpFoundation\RedirectResponse
     */
    public function removeAction($chainId)
    {
        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.not_exist'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        if (!$this->checkOwner($chain)) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.access_denied'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        $em->remove($chain);
        $em->flush();

        $this->addFlash('success', $this->get('translator')->trans('thought.chain.successfully-remove'));

        return $this->redirect($this->generateUrl('sonata_user_chains'));
    }

    /**
     * @Route("/chain/{chainId}/share/{share}", name="sonata_user_chain_share", requirements={"chainId"="\d+", "share"="0|1"})
     *
     * @param int $chainId
     * @param int $share
     * @return \Symfony\Component\HttpFoundation\RedirectResponse
     */
    public function shareAction($chainId, $share)
    {
        $em = $this->getDoctrine()->getManager();

        $share = $share ? false: true;

        $shareMessage = $share ? 'successfully-private' : 'successfully-shared';

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.not_exist'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        if (!$this->checkOwner($chain)) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.access_denied'));

            return $this->redirect($this->generateUrl('sonata_user_chains'));
        }

        $chain->setIsPrivate($share);
        $em->persist($chain);
        $em->flush();

        $this->addFlash('success', $this->get('translator')->trans('thought.chain.' . $shareMessage));

        return $this->redirect($this->generateUrl('sonata_user_chains'));
    }

    /**
     * @Route("/shared-chains", name="sonata_user_shared_chains")
     *
     * @param Request $request
     * @return Response
     */
    public function listSharedAction(Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $chains = $em->getRepository('ThoughtBundle:Chain')->getAllSharedChains();

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $chains,
            $request->query->getInt('page', 1),
            10
        );

        return $this->render('ApplicationSonataUserBundle:Chain:sharedList.html.twig', array(
            'chains' => $pagination,
        ));
    }

    /**
     * Check owner chain
     *
     * @param Chain $chain
     * @return bool
     */
    private function checkOwner(Chain $chain)
    {
        return $chain->getUser()->getId() == $this->getUser()->getId() ? true : false;
    }
}
